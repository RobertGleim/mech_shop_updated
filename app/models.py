import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from datetime import date, datetime



class Base(DeclarativeBase):
    pass





# customers: name, email. phone, address, id, password
# service tickets: id, cutomers, mechanics, service disc, price, vin
# mechanics: username, password, email, salary, address, id

db = SQLAlchemy(model_class=Base)






 #  =========================================================================
class Customers(Base):
    __tablename__ = 'customers'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(120),nullable=False,)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(360), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    
    
    service_tickets: Mapped[list['Service_Ticket']] = relationship('Service_Ticket', back_populates='customer')
    invoices: Mapped[list['Invoice']] = relationship('Invoice', back_populates='customer')
 #  =========================================================================    
class Service_Ticket(Base):
    __tablename__ = 'service_tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('customers.id'), nullable=True) #made true for testing
    service_description: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    vin: Mapped[str] = mapped_column(String(20), nullable=False)
    service_date: Mapped[Date] = mapped_column(Date, default=lambda: date.today(), nullable=False)

    
    mechanics: Mapped[list['Mechanics']] = relationship('Mechanics', secondary='ticket_mechanics', back_populates='service_tickets')
    customer: Mapped['Customers'] = relationship(
        'Customers', back_populates='service_tickets')
    invoices: Mapped[list['Invoice']] = relationship('Invoice', back_populates='service_ticket')
    
    
 #  =========================================================================    
class Ticket_Mechanics(Base):
    __tablename__ = 'ticket_mechanics'
    
    service_ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey('service_tickets.id'), primary_key=True)
    
    mechanic_id: Mapped[int] = mapped_column(Integer, ForeignKey('mechanics.id'), primary_key=True)

    
 #  =========================================================================
      
    
class Mechanics(Base):
    __tablename__ = 'mechanics'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(360), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    salary: Mapped[float] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    is_admin: Mapped[bool] = mapped_column(nullable=False, default=False)

    service_tickets: Mapped[list['Service_Ticket']] = relationship(
        'Service_Ticket',
        secondary='ticket_mechanics',
        back_populates='mechanics'
    )

#  =========================================================================
class ItemsDescription(Base):
    __tablename__ = 'items_description'

    id: Mapped[int] = mapped_column(primary_key=True)
    part_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    part_description: Mapped[str] = mapped_column(String(500), nullable=False)
    part_price: Mapped[float] = mapped_column(Float, nullable=False)
    

    inventory_items: Mapped[list['InventoryItem']] = relationship('InventoryItem', back_populates='items_description')
   
#  =========================================================================
class InventoryItem(Base):
    __tablename__ = 'inventory'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    items_description_id: Mapped[int] = mapped_column(
    Integer, ForeignKey('items_description.id'), nullable=False)

    items_description: Mapped['ItemsDescription'] = relationship('ItemsDescription', back_populates='inventory_items')

    invoice_inventory_links: Mapped[list["Invoice_Inventory_Link"]] = relationship(
        'Invoice_Inventory_Link',
        back_populates="inventory_item",
        cascade="all, delete-orphan",
        foreign_keys=lambda: [Invoice_Inventory_Link.inventory_item_id],
        overlaps='invoices')

    invoices: Mapped[list['Invoice']] = relationship(
        'Invoice',
        secondary='invoice_inventory_link',
        back_populates='inventory_items',
        foreign_keys=lambda: [Invoice_Inventory_Link.invoice_id, Invoice_Inventory_Link.inventory_item_id],
        overlaps='inventory_item, invoice_inventory_links')
    
    
#  =========================================================================

class Invoice_Inventory_Link(Base):
    __tablename__ = 'invoice_inventory_link'

    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('invoices.id'), primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(
    Integer, ForeignKey('inventory.id'), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    
    invoice: Mapped['Invoice'] = relationship(
    'Invoice',back_populates='invoice_inventory_links',foreign_keys=[invoice_id], overlaps="invoices")
    inventory_item: Mapped['InventoryItem'] = relationship('InventoryItem', back_populates='invoice_inventory_links',foreign_keys=[inventory_item_id], overlaps="invoices")     

    
#  =========================================================================
class Invoice(Base):
    __tablename__ = 'invoices'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('customers.id'), nullable=True) #made true for testing
    service_ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey('service_tickets.id'), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    
    invoice_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=True)
    submitted: Mapped[bool] = mapped_column(nullable=False, default=False)
    

    customer: Mapped['Customers'] = relationship('Customers', back_populates='invoices')
    service_ticket: Mapped['Service_Ticket'] = relationship('Service_Ticket', back_populates='invoices')

    invoice_inventory_links: Mapped[list["Invoice_Inventory_Link"]] = relationship('Invoice_Inventory_Link',back_populates="invoice",cascade="all, delete-orphan",foreign_keys="[Invoice_Inventory_Link.invoice_id]", overlaps="inventory_items")

    inventory_items: Mapped[list["InventoryItem"]] = relationship("InventoryItem",secondary="invoice_inventory_link",back_populates="invoices",foreign_keys="[Invoice_Inventory_Link.invoice_id, Invoice_Inventory_Link.inventory_item_id]", overlaps="invoice, invoice_inventory_links, inventory_item")

