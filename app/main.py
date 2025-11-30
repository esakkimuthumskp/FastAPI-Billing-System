import os
from fastapi import FastAPI, Request, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, select
from .database import engine, get_session
from . import models, crud, seed, email_utils, utils
from .models import Product, Denomination, Purchase, PurchaseItem, PurchaseChange

app = FastAPI()

templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    seed.seed()


@app.get("/billing", response_class=HTMLResponse)
def billing_page(request: Request):
    with Session(engine) as session:
        products = crud.list_products(session)
        denominations = crud.list_denominations(session)
        return templates.TemplateResponse("billing.html", {"request": request, "products": products, "denominations": denominations})


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/generate", response_class=HTMLResponse)
async def generate_bill(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    customer_email = form.get("customer_email")
    paid_amount = float(form.get("paid_amount", 0))
    product_ids = form.getlist("product_id")
    quantities = form.getlist("quantity")

    # parse denominations available in shop and paid by customer
    denominations_in_shop = []
    paid_denominations = []
    for key, val in form.multi_items():
        if key.startswith("denom_"):
            denom = int(key.split("_")[1])
            count = int(val)
            denominations_in_shop.append((denom, count))
            if count > 0:
                paid_denominations.append((denom, count))

    # build items
    items = []
    subtotal = 0.0
    total_tax = 0.0
    total = 0.0

    with Session(engine) as session:
        # validate and compute
        product_list = []
        for pid, qty_str in zip(product_ids, quantities):
            qty = int(qty_str)
            prod = crud.get_product_by_product_id(session, pid)
            if not prod:
                return HTMLResponse(f"Product {pid} not found", status_code=400)
            if qty > prod.available_stocks:
                return HTMLResponse(f"Insufficient stock for {prod.name}", status_code=400)
            line_sub = prod.price_per_unit * qty
            line_tax = line_sub * (prod.tax_percentage / 100.0)
            line_total = line_sub + line_tax
            subtotal += line_sub
            total_tax += line_tax
            total += line_total
            product_list.append((prod, qty, line_sub, line_tax, line_total))

        # Allow paid_amount < total; balance payable to customer will be negative or zero

        change_amount = round(paid_amount - total, 2)

        # denominations calculation requires integer arithmetic; assume denominations are in whole units
        # convert to integer minimal units (like cents) if needed; here we operate in integer rupee-like units
        change_int = int(round(change_amount))

        # sort denominations desc
        denominations_in_shop.sort(key=lambda x: x[0], reverse=True)
        change_map = utils.calculate_change_bounded(denominations_in_shop, change_int)
        if change_int > 0 and not change_map:
            return HTMLResponse(f"Unable to return change with available denominations", status_code=400)

        # create purchase and items
        purchase = Purchase(customer_email=customer_email, subtotal=subtotal, tax=total_tax, total=total, paid_amount=paid_amount, change_amount=change_amount)
        item_objs = []
        change_objs = []
        for prod, qty, line_sub, line_tax, line_total in product_list:
            item = PurchaseItem(product_id=prod.product_id, product_name=prod.name, unit_price=prod.price_per_unit, quantity=qty, tax_percentage=prod.tax_percentage, line_subtotal=line_sub, line_tax=line_tax, line_total=line_total)
            item_objs.append(item)
            crud.decrease_stock(session, prod, qty)
        for val, cnt in change_map.items():
            change_objs.append(PurchaseChange(denomination_value=val, count=cnt))

        paid_denom_objs = []
        for val, cnt in paid_denominations:
            paid_denom_objs.append(models.PurchasePaidDenomination(denomination_value=val, count=cnt))

        session.add(purchase)
        session.commit()
        session.refresh(purchase)
        for it in item_objs:
            it.purchase_id = purchase.id
            session.add(it)
        for ch in change_objs:
            ch.purchase_id = purchase.id
            session.add(ch)
        for pd in paid_denom_objs:
            pd.purchase_id = purchase.id
            session.add(pd)
        session.commit()

        # background email
        smtp_config = {
            "SMTP_HOST": os.getenv("SMTP_HOST"),
            "SMTP_PORT": os.getenv("SMTP_PORT"),
            "SMTP_USERNAME": os.getenv("SMTP_USERNAME"),
            "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
            "SMTP_FROM": os.getenv("SMTP_FROM", os.getenv("SMTP_USERNAME"))
        }

        # generate pdf bytes synchronously
        items_for_pdf = session.exec(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase.id)).all()
        pdf_bytes = email_utils.generate_invoice_pdf_bytes(purchase, items_for_pdf)

        # schedule send
        if smtp_config.get("SMTP_HOST"):
            background_tasks.add_task(email_utils.send_invoice_email, smtp_config, customer_email, f"Invoice #{purchase.id}", f"Please find attached invoice #{purchase.id}", pdf_bytes, f"invoice_{purchase.id}.pdf")

        # render summary page
        changes = session.exec(select(PurchaseChange).where(PurchaseChange.purchase_id == purchase.id)).all()
        paid_denom_db = session.exec(select(models.PurchasePaidDenomination).where(models.PurchasePaidDenomination.purchase_id == purchase.id)).all()
        items_saved = items_for_pdf
        return templates.TemplateResponse("summary.html", {
            "request": request,
            "purchase": purchase,
            "items": items_saved,
            "changes": changes,
            "paid_denominations": [(pd.denomination_value, pd.count) for pd in paid_denom_db]
        })


@app.get("/bill/{purchase_id}", response_class=HTMLResponse)
def bill_detail(request: Request, purchase_id: int):
    with Session(engine) as session:
        purchase = session.get(Purchase, purchase_id)
        if not purchase:
            return HTMLResponse("Not found", status_code=404)
        items = session.exec(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id)).all()
        changes = session.exec(select(PurchaseChange).where(PurchaseChange.purchase_id == purchase_id)).all()
        return templates.TemplateResponse("purchase_detail.html", {"request": request, "purchase": purchase, "items": items, "changes": changes})


@app.get("/customers", response_class=HTMLResponse)
def customers_page(request: Request):
    return templates.TemplateResponse("purchases.html", {"request": request, "purchases": None})


@app.get("/products", response_class=HTMLResponse)
def products_page(request: Request):
    with Session(engine) as session:
        products = crud.list_products(session)
        return templates.TemplateResponse("products.html", {"request": request, "products": products})


@app.post("/products/add")
async def add_product(request: Request):
    form = await request.form()
    product_id = form.get('product_id')
    name = form.get('name')
    available_stocks = int(form.get('available_stocks') or 0)
    price_per_unit = float(form.get('price_per_unit') or 0)
    tax_percentage = float(form.get('tax_percentage') or 0)
    with Session(engine) as session:
        # simple uniqueness check
        exists = session.exec(select(Product).where(Product.product_id == product_id)).first()
        if exists:
            # redirect back to products page (could show flash message)
            return RedirectResponse(url='/products', status_code=303)
        prod = Product(product_id=product_id, name=name, available_stocks=available_stocks, price_per_unit=price_per_unit, tax_percentage=tax_percentage)
        session.add(prod)
        session.commit()
    return RedirectResponse(url='/products', status_code=303)


@app.post("/customers/search", response_class=HTMLResponse)
async def search_customers(request: Request):
    form = await request.form()
    email = form.get('customer_email')
    with Session(engine) as session:
        purchases = session.exec(select(Purchase).where(Purchase.customer_email == email).order_by(Purchase.created_at.desc())).all()
        return templates.TemplateResponse("purchases.html", {"request": request, "purchases": purchases})

@app.get("/products/edit/{product_id}", response_class=HTMLResponse)
def edit_product_page(request: Request, product_id: str):
    with Session(engine) as session:
        product = crud.get_product_by_product_id(session, product_id)
        if not product:
            return RedirectResponse(url='/products', status_code=303)
        return templates.TemplateResponse("product_edit.html", {"request": request, "product": product})

@app.post("/products/edit/{product_id}")
async def edit_product(request: Request, product_id: str):
    form = await request.form()
    name = form.get('name')
    available_stocks = int(form.get('available_stocks') or 0)
    price_per_unit = float(form.get('price_per_unit') or 0)
    tax_percentage = float(form.get('tax_percentage') or 0)
    with Session(engine) as session:
        product = crud.get_product_by_product_id(session, product_id)
        if not product:
            return RedirectResponse(url='/products', status_code=303)
        product.name = name
        product.available_stocks = available_stocks
        product.price_per_unit = price_per_unit
        product.tax_percentage = tax_percentage
        session.add(product)
        session.commit()
    return RedirectResponse(url='/products', status_code=303)


@app.post("/products/delete/{product_id}")
async def delete_product(request: Request, product_id: str):
    with Session(engine) as session:
        product = crud.get_product_by_product_id(session, product_id)
        if product:
            session.delete(product)
            session.commit()
    return RedirectResponse(url='/products', status_code=303)