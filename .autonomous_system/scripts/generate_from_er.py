import os
import re
from collections import defaultdict

def parse_er_schema(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Parse entities
    entities = {}
    entity_blocks = re.findall(r'(\w+)\s*\{\s*([^}]*)\}', content)
    for entity_name, block in entity_blocks:
        columns = []
        for line in block.split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                col_type = parts[0]
                col_name = parts[1]
                modifiers = parts[2:] if len(parts) > 2 else []
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'is_pk': 'PK' in modifiers,
                    'is_fk': 'FK' in modifiers
                })
        entities[entity_name] = columns

    # Parse relationships
    relationships = []
    rel_lines = re.findall(r'(\w+)\s+(\|\|--o\{|\|\|--\|\||\}o--\|\|)\s+(\w+)\s+:\s+"([^"]*)"', content)
    for ent1, rel_type, ent2, rel_name in rel_lines:
        relationships.append({
            'source': ent1,
            'target': ent2,
            'type': rel_type,
            'name': rel_name
        })

    return entities, relationships

def map_type_to_sqlalchemy(t):
    t = t.lower()
    if t == 'uuid': return 'UUID(as_uuid=True)'
    if t == 'string': return 'String'
    if t == 'boolean': return 'Boolean'
    if t == 'int': return 'Integer'
    if t == 'timestamp': return 'DateTime'
    if t == 'text': return 'Text'
    if t == 'json': return 'JSON'
    if t == 'decimal': return 'Float'
    if t == 'float': return 'Float'
    if t == 'date': return 'Date'
    if t == 'enum': return 'String'
    return 'String'

def map_type_to_python(t):
    t = t.lower()
    if t == 'uuid': return 'UUID'
    if t == 'string': return 'str'
    if t == 'boolean': return 'bool'
    if t == 'int': return 'int'
    if t == 'timestamp': return 'datetime'
    if t == 'text': return 'str'
    if t == 'json': return 'dict'
    if t == 'decimal': return 'float'
    if t == 'float': return 'float'
    if t == 'date': return 'date'
    if t == 'enum': return 'str'
    return 'str'

def generate_models(entities, relationships, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # Pre-calculate relationships per entity
    entity_rels = defaultdict(list)
    for rel in relationships:
        if rel['type'] == '||--o{':
            entity_rels[rel['source']].append({'target': rel['target'], 'uselist': True, 'back_populates': rel['source'].lower()})
            entity_rels[rel['target']].append({'target': rel['source'], 'uselist': False, 'back_populates': rel['target'].lower() + "s"})
        elif rel['type'] == '||--||':
            entity_rels[rel['source']].append({'target': rel['target'], 'uselist': False, 'back_populates': rel['source'].lower()})
            entity_rels[rel['target']].append({'target': rel['source'], 'uselist': False, 'back_populates': rel['target'].lower()})

    for entity_name, columns in entities.items():
        file_name = f"{entity_name.lower()}.py"
        file_path = os.path.join(output_dir, file_name)
        
        lines = [
            "import uuid",
            "from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Date, Text, JSON, ForeignKey",
            "from sqlalchemy.orm import relationship",
            "from datetime import datetime, date",
            "from sqlalchemy.dialects.postgresql import UUID",
            "from app.db.database import Base",
            "",
            f"class {entity_name}(Base):",
            f"    __tablename__ = '{entity_name.lower()}s'", 
            ""
        ]
        
        has_id = False
        for col in columns:
            col_mapped_type = map_type_to_sqlalchemy(col['type'])
            args = [col_mapped_type]
            if col['is_pk']:
                args.append("primary_key=True")
                if col['type'] == 'uuid':
                    args.append("default=uuid.uuid4")
                    args.append("index=True")
                has_id = True
            
            if col['is_fk']:
                # Simple guess for foreign key target table based on column name like 'user_id' -> 'users.id'
                # or relation target
                target_table = col['name'].replace('_id', 's')
                if target_table.endswith('ys'): target_table = target_table[:-2] + 'ies'
                
                # Check directly in entities if there's a match
                possible_entity = next((e for e in entities if col['name'] == e.lower() + "_id"), None)
                if possible_entity:
                    target_table = possible_entity.lower() + "s"
                    
                args.append(f"ForeignKey('{target_table}.id')")
                args.append("index=True")
                
            line = f"    {col['name']} = Column({', '.join(args)})"
            lines.append(line)
            
        lines.append("")
        
        # Add relationships
        if entity_name in entity_rels:
            lines.append("    # Relationships")
            for rel in entity_rels[entity_name]:
                rel_attr = rel['target'].lower() + "s" if rel['uselist'] else rel['target'].lower()
                lines.append(f"    {rel_attr} = relationship('{rel['target']}', back_populates='{rel['back_populates']}')")
                
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
            

def generate_schemas(entities, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    for entity_name, columns in entities.items():
        file_name = f"{entity_name.lower()}.py"
        file_path = os.path.join(output_dir, file_name)
        
        lines = [
            "from typing import Optional, List, Any, Dict",
            "from datetime import datetime, date",
            "from pydantic import BaseModel",
            "from uuid import UUID",
            "",
            f"class {entity_name}Base(BaseModel):"
        ]
        
        has_fields = False
        for col in columns:
            if col['name'] in ['id', 'created_at', 'updated_at', 'deleted_at']:
                continue # Skip auto fields in Base
            py_type = map_type_to_python(col['type'])
            lines.append(f"    {col['name']}: Optional[{py_type}] = None")
            has_fields = True
            
        if not has_fields:
            lines.append("    pass")
            
        lines.extend([
            "",
            f"class {entity_name}Create({entity_name}Base):",
            "    pass",
            "",
            f"class {entity_name}Update(BaseModel):"
        ])
        
        has_fields = False
        for col in columns:
            if col['name'] in ['id', 'created_at', 'updated_at', 'deleted_at']:
                continue
            py_type = map_type_to_python(col['type'])
            lines.append(f"    {col['name']}: Optional[{py_type}] = None")
            has_fields = True
            
        if not has_fields:
            lines.append("    pass")
            
        lines.extend([
            "",
            f"class {entity_name}Response({entity_name}Base):",
            "    id: UUID",
            "    created_at: Optional[datetime] = None",
            "    updated_at: Optional[datetime] = None",
            "",
            "    class Config:",
            "        from_attributes = True"
        ])
        
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))


if __name__ == '__main__':
    er_path = 'elk_schema.txt'
    models_dir = 'app/models/elk_models'
    schemas_dir = 'app/schemas/elk_schemas'
    
    entities, relationships = parse_er_schema(er_path)
    generate_models(entities, relationships, models_dir)
    generate_schemas(entities, schemas_dir)
    print(f"Generated {len(entities)} models and schemas.")
