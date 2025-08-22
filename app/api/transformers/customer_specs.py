from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.api.transformers.base import MappingSpec, FieldRule, GenericTransformer
from app.api.schemas.customer import CanonicalBusinessPartner, CanonicalCustomerEmployees, CanonicalCustomerAddress, SAPBPAddresses, SAPBPContactEmployees, SAPBusinessPartner

bp_a2c = MappingSpec(
    dest_model=CanonicalBusinessPartner,
    fields={
        "card_code":         FieldRule(source="lcard_code"),
        "card_name":         FieldRule(source="lcard_name"),
        "card_foreign_name": FieldRule(source="lcard_foreign_name"),
        "card_type":         FieldRule(source="lcard_type"),
        "group_code":        FieldRule(source="lgroup_code"),
        "federal_tax_id":    FieldRule(source="lfederal_tax_id"),
        "additional_id":     FieldRule(source="ladditional_id"),
        "unified_federal_tax_id": FieldRule(source="lunified_federal_tax_id"),
        "country":           FieldRule(source="lcountry"),
        "u_tipo_cont":       FieldRule(source="lu_tipo_cont"),
        "u_tipo_sn":         FieldRule(source="lu_tipo_sn"),
        "u_doc_identificacion": FieldRule(source="lu_doc_identificacion"),
        "sales_person_code": FieldRule(source="lsales_person_code"),
        "contact_employees": FieldRule(
            source="lcontact_employees", many=True,
            nested=MappingSpec(
                dest_model=CanonicalCustomerEmployees,
                fields={
                    "name":    FieldRule(source="lname"),
                    "address": FieldRule(source="laddress"),
                    "e_mail":  FieldRule(source="le_mail"),
                    "phone_1": FieldRule(source="lphone_1"),
                },
            ),
        ),
        "bp_addresses": FieldRule(
            source="lbp_addresses", many=True,
            nested=MappingSpec(
                dest_model=CanonicalCustomerAddress,
                fields={
                    "address_name":        FieldRule(source="laddress_name"),
                    "address_name_2":      FieldRule(source="laddress_name_2"),
                    "address_name_3":      FieldRule(source="laddress_name_3"),
                    "address_type":        FieldRule(source="laddress_type"),
                    "county":              FieldRule(source="lcounty"),
                    "country":             FieldRule(source="lcountry"),
                    "state":               FieldRule(source="lstate"),
                    "zipcode":             FieldRule(source="lzipcode"),
                    "building_floor_room": FieldRule(source="lbuilding_floor_room"),
                    "street":              FieldRule(source="lstreet"),
                    "block":               FieldRule(source="lblock"),
                    "city":                FieldRule(source="lcity"),
                },
            ),
        ),
        "notes": FieldRule(source="lnotes"),
    },
)

bp_c2b = MappingSpec(
    dest_model=SAPBusinessPartner,
    fields={
        "card_code":         FieldRule(source="card_code"),
        "card_name":         FieldRule(source="card_name"),
        "card_foreign_name": FieldRule(source="card_foreign_name"),
        "card_type":         FieldRule(source="card_type"),
        "group_code":        FieldRule(source="group_code"),
        "federal_tax_id":    FieldRule(source="federal_tax_id"),
        "additional_id":     FieldRule(source="additional_id"),
        "unified_federal_tax_id": FieldRule(source="unified_federal_tax_id"),
        "country":           FieldRule(source="country"),
        "u_tipo_cont":       FieldRule(source="u_tipo_cont"),
        "u_tipo_sn":         FieldRule(source="u_tipo_sn"),
        "u_doc_identificacion": FieldRule(source="u_doc_identificacion"),
        "sales_person_code": FieldRule(source="sales_person_code"),
        "contact_employees": FieldRule(
            source="contact_employees", many=True,
            nested=MappingSpec(
                dest_model=SAPBPContactEmployees,
                fields={
                    "name":    FieldRule(source="name"),
                    "address": FieldRule(source="address"),
                    "e_mail":  FieldRule(source="e_mail"),
                    "phone1":  FieldRule(source="phone_1"),
                },
            ),
        ),
        "bp_addresses": FieldRule(
            source="bp_addresses", many=True,
            nested=MappingSpec(
                dest_model=SAPBPAddresses,
                fields={
                    "address_name":        FieldRule(source="address_name"),
                    "address_name2":       FieldRule(source="address_name_2"),
                    "address_name3":       FieldRule(source="address_name_3"),
                    "address_type":        FieldRule(source="address_type"),
                    "county":              FieldRule(source="county"),
                    "country":             FieldRule(source="country"),
                    "state":               FieldRule(source="state"),
                    "zipcode":             FieldRule(source="zipcode"),
                    "building_floor_room": FieldRule(source="building_floor_room"),
                    "street":              FieldRule(source="street"),
                    "block":               FieldRule(source="block"),
                    "city":                FieldRule(source="city"),
                },
            ),
        ),
        "notes": FieldRule(source="notes"),
    },
)

bp_transformer = GenericTransformer(bp_a2c, bp_c2b)
