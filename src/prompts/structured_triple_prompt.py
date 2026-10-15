class Prompt:
    """
    Enhanced prompt for structured spreadsheet data → knowledge graph conversion
    """

    STRUCTURED_DATA_TRIPLE_PROMPT = """
        You are a specialized knowledge graph extraction system for STRUCTURED SPREADSHEET DATA.
    
        **IMPORTANT: This is NOT unstructured text - this is structured tabular data with defined columns and relationships.**
    
        **Your Mission:**
        Convert structured spreadsheet records into meaningful knowledge graph triples that preserve the semantic relationships between columns.
    
        **Understanding Structured Data:**
        - Each row represents a connected entity or record
        - Column headers define the relationship types
        - Values in the same row are semantically connected
        - Look for entity-attribute and entity-relationship patterns
    
        **Extraction Rules for Spreadsheet Data:**
    
        1. **Identify Entity Columns** (usually names, IDs, titles):
           - Person names, company names, product names, etc.
           - These become your primary subjects/objects
    
        2. **Identify Relationship Columns** (roles, positions, categories):
           - Job titles, departments, categories, types
           - These define HOW entities connect
    
        3. **Identify Attribute Columns** (properties, values, descriptions):
           - Ages, salaries, dates, quantities, descriptions
           - These become entity properties
    
        **Triple Generation Patterns:**
    
        For a record like: Name=John, Role=Engineer, Company=Google, Experience=5 years
    
        Generate triples like:
        - {subject: "John", predicate: "works_as", object: "Engineer"}
        - {subject: "John", predicate: "works_at", object: "Google"}  
        - {subject: "John", predicate: "has_experience", object: "5 years"}
        - {subject: "Google", predicate: "employs", object: "John"}
        - {subject: "Engineer", predicate: "employed_by", object: "Google"}
    
        **Output Format:**
        Return a JSON array of triples with exactly these keys:
        - "subject": the main entity (string)
        - "predicate": the relationship type (string) 
        - "object": the connected entity or value (string)
    
        **Quality Guidelines:**
        - Create bidirectional relationships when logical
        - Use clear, descriptive predicates (works_at, has_role, belongs_to)
        - Connect entities within the same record
        - Avoid vague relationships like "relates_to"
    
        **STRUCTURED DATA TO ANALYZE:**
        """

    @staticmethod
    def create_structured_prompt(schema_headers, record_data) -> tuple[str, str]:
        """
        Create a schema-aware prompt for structured data
        """

        # Add schema context
        prompt = f"\n**SCHEMA:** {', '.join(schema_headers)}\n"

        # Add record data
        prompt += "**RECORD DATA:**\n"
        for header, value in record_data.items():
            if value:
                prompt += f"- {header}: {value}\n"

        prompt += "\n**Extract meaningful triples that represent the relationships in this structured record:**"

        return Prompt.STRUCTURED_DATA_TRIPLE_PROMPT, prompt
