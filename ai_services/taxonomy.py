from sqlalchemy.orm import Session
from models.enums import EnumValue
from models.reference import OperationalActivity, SubArea

def get_ai_taxonomy(db: Session):
    """
    Fetches all necessary dropdown values from the database to ground the AI model.
    Returns a dict with categories as keys and lists of strings as values.
    """
    # Fetch all EnumValues
    enums = db.query(EnumValue).all()
    
    # Organize by category
    taxonomy = {}
    for e in enums:
        cat = e.category
        if cat not in taxonomy:
            taxonomy[cat] = []
        taxonomy[cat].append(e.value)
        
    # Special handling for subgroups (which have parents)
    subgroup_mapping = {}
    subgroups = [e for e in enums if e.category == "incident_subgroup"]
    for s in subgroups:
        parent = s.parent_value
        if parent:
            if parent not in subgroup_mapping:
                subgroup_mapping[parent] = []
            subgroup_mapping[parent].append(s.value)
    
    # Fetch Operational Activities
    activities = db.query(OperationalActivity).all()
    taxonomy["operational_activities"] = [a.name for a in activities]
    
    # Fetch Areas and Sub-Areas
    areas = db.query(SubArea.area_name.distinct()).all()
    taxonomy["areas"] = [a[0] for a in areas]
    
    # Add rules hierarchy
    taxonomy["subgroup_rules"] = subgroup_mapping
    
    return taxonomy
