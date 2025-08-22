
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date, Float, ForeignKey, Integer, String
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
 #  =========================================================================    
class Service_Ticket(Base):
    __tablename__ = 'service_tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('customers.id'), nullable=False)
    service_description: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    vin: Mapped[str] = mapped_column(String(20), nullable=False)
    service_date: Mapped[Date] = mapped_column(Date, default=lambda: date.today(), nullable=False)

    
    mechanics: Mapped[list['Mechanics']] = relationship(
        'Mechanics',
        secondary='ticket_mechanics',
        back_populates='service_tickets'
    )
    customer: Mapped['Customers'] = relationship(
        'Customers', back_populates='service_tickets'
    )
    
    
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