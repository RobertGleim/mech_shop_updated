
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from datetime import date


# customers: name, email. phone, address, id, password
# service tickets: id, cutomers, mechanics, service disc, price, vin
# mechanics: username, password, email, salary, address, id



class Base(DeclarativeBase):
    pass

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
    password: Mapped[str] = mapped_column(String(120), nullable=False)
    
    
    service_tickets: Mapped[list['Service_Ticket']] = relationship('Service_Ticket', back_populates='customer')
    invoices: Mapped[list['Invoice']] = relationship('Invoice', back_populates='customer')
 #  =========================================================================    
class Service_Ticket(Base):
    __tablename__ = 'service_tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('customers.id'), nullable=False)
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
    password: Mapped[str] = mapped_column(String(120), nullable=False)
    salary: Mapped[float] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)

    service_tickets: Mapped[list['Service_Ticket']] = relationship(
        'Service_Ticket',
        secondary='ticket_mechanics',
        back_populates='mechanics'
    )

#  =========================================================================
class ItemsDescription(Base):
    __tablename__ = 'items_description'

    id: Mapped[int] = mapped_column(primary_key=True)
    part_name: Mapped[str] = mapped_column(String(100), nullable=False)
    part_desc: Mapped[str] = mapped_column(String(250), nullable=False)
    quantity_in_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    inventory_items: Mapped[list['Inventory']] = relationship('Inventory', back_populates='inventory_description')
    invoices: Mapped[list['Invoice']] = relationship('Invoice', secondary='inventory', back_populates='items_description')

#  =========================================================================
class Inventory(Base):
    __tablename__ = 'inventory'

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(Integer, ForeignKey('items_description.id'), nullable=False)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('invoices.id'), nullable=False)
    
    inventory_description: Mapped['ItemsDescription'] = relationship('ItemsDescription', back_populates='inventory')
    
    invoice: Mapped['Invoice'] = relationship('Invoice', back_populates='inventory')

#  =========================================================================
class Invoice(Base):
    __tablename__ = 'invoices'

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('customers.id'), nullable=False)
    service_ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey('service_tickets.id'), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    invoice_date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now, nullable=True)
    submitted: Mapped[bool] = mapped_column(nullable=False, default=False)

    inventory_items: Mapped[list['Inventory']] = relationship('Inventory',  back_populates='invoices')
    
    customer: Mapped['Customers'] = relationship('Customers', back_populates='invoices')
    service_ticket: Mapped['Service_Ticket'] = relationship('Service_Ticket', back_populates='invoices')
    inventory_items: Mapped[list['Inventory']] = relationship('Inventory', back_populates='invoice')
    items_description: Mapped[list['ItemsDescription']] = relationship('ItemsDescription', secondary='inventory', back_populates='invoices')