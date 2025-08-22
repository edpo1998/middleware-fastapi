from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# A) Input Logistas

class CustomerEmployees(BaseModel):
    lname: str
    laddress: str
    le_mail: Optional[str] 
    lphone_1: Optional[str] 

class CustomerAddress(BaseModel):
    laddress_name: str
    laddress_name_2: Optional[str] 
    laddress_name_3: Optional[str] 
    laddress_type: str
    lcounty: str
    lcountry: str
    lstate: str
    lzipcode: Optional[str] 
    lbuilding_floor_room: str
    lstreet: str
    lblock: str
    lcity: str

class CustomerCreate(BaseModel):
    lcard_code: str
    lcard_name: str
    lcard_foreign_name: str
    lcard_type: str
    lgroup_code: int
    lfederal_tax_id: Optional[str] 
    ladditional_id: str
    lunified_federal_tax_id: Optional[str] 
    lcountry: str
    lu_tipo_cont: Optional[str] 
    lu_tipo_sn: Optional[str] = None
    lu_doc_identificacion: str = None
    lsales_pearson_code: str = None
    lcontact_employees: List[CanonicalCustomerEmployees]
    lbp_addresses: List[CanonicalCustomerAddress]
    lnotes: Optional[str] = None



# C) Modelo Canonico

class CanonicalCustomerEmployees(BaseModel):
    name: str
    address: str
    e_mail: Optional[str] 
    phone_1: Optional[str] 

class CanonicalCustomerAddress(BaseModel):
    address_name: str
    address_name_2: Optional[str] 
    address_name_3: Optional[str] 
    address_type: str
    county: str
    country: str
    state: str
    zipcode: Optional[str] 
    building_floor_room: str
    street: str
    block: str
    city: str

class CanonicalBusinessPartner(BaseModel):
    card_code: str
    card_name: str
    card_foreign_name: str
    card_type: str
    group_code: int
    federal_tax_id: Optional[str]
    additional_id: str
    unified_federal_tax_id: Optional[str]
    country: str
    u_tipo_cont: Optional[str]
    u_tipo_sn: Optional[str] = None
    u_doc_identificacion: Optional[str] = None
    sales_pearson_code: str = None
    contact_employees: List[CanonicalCustomerEmployees]
    bp_addresses: List[CanonicalCustomerAddress]
    notes: Optional[str] = None


# SAP Interfaces whit alias

class SAPBPContactEmployees(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(..., alias="Name")
    address: str = Field(..., alias="Address")
    e_mail: Optional[str] = Field(None, alias="E_Mail")
    phone1: Optional[str] = Field(None, alias="Phone1")

class SAPBPAddresses(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    address_name: str = Field(..., alias="AddressName")
    address_name2: Optional[str] = Field(None, alias="AddressName2")
    address_name3: Optional[str] = Field(None, alias="AddressName3")
    address_type: str = Field(..., alias="AddressType")
    county: str = Field(..., alias="County")
    country: str = Field(..., alias="Country")
    state: str = Field(..., alias="State")
    zipcode: Optional[str] = Field(None, alias="ZipCode")
    building_floor_room: str = Field(..., alias="BuildingFloorRoom")
    street: str = Field(..., alias="Street")
    block: str = Field(..., alias="Block")
    city: str = Field(..., alias="City")

class SAPBusinessPartner(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    card_code: str = Field(..., alias="CardCode")
    card_name: str = Field(..., alias="CardName")
    card_foreign_name: str = Field(..., alias="CardForeignName")
    card_type: str = Field(..., alias="CardType")
    group_code: int = Field(..., alias="GroupCode")
    federal_tax_id: Optional[str] = Field(None, alias="FederalTaxID")
    additional_id: str = Field(..., alias="AdditionalID")
    unified_federal_tax_id: Optional[str] = Field(None, alias="UnifiedFederalTaxID")
    country: str = Field(..., alias="Country")
    u_tipo_cont: Optional[str] = Field(None, alias="U_TipoCont")
    u_tipo_sn: Optional[str] = Field(None, alias="U_TipoSN")
    u_doc_identificacion: Optional[str] = Field(None, alias="U_DocIdentificacion")
    sales_person_code: Optional[int] = Field(None, alias="SalesPersonCode")
    contact_employees: List[SAPBPContactEmployees] = Field(..., alias="ContactEmployees")
    bp_addresses: List[SAPBPAddresses] = Field(..., alias="BPAddresses")
    notes: Optional[str] = Field(None, alias="Notes")
