"""
RAG_FILES - Google Sheets Retrieval-Augmented Generation (RAG) Module

This module provides functionality for integrating Google Sheets with Retrieval-Augmented Generation (RAG) workflows.
It enables efficient data retrieval and augmentation from Google Sheets, supporting AI-driven applications.

Features:
- Connects to Google Sheets using secure authentication
- Retrieves and processes sheet data for RAG pipelines
- Designed for extensibility and integration with other RAG components

Usage:
Import this module in your project to leverage Google Sheets as a data source for RAG-based solutions.

Author: PIRATE-E
License: MIT
"""

from bs4 import BeautifulSoup


class GoogleSheetsRAG:
    def __init__(self, sheets_url: str, schema_config: dict = None):
        self.sheets_url = sheets_url.split("edit?")[0].__add__("htmlview")
        self.data = []
        self.chunking_size: int = 0
        self.schema_config = schema_config or {}
        self.headers = []
        self.structured_data = []

    class LoadWebContent:
        """Load web content from the provided Google Sheets URL"""

        def __init__(self, sheets_url):
            self.sheets_url = sheets_url

        def load_web_content(self) -> str:
            """Production-ready Google Sheets loading with multiple fallback strategies"""
            from playwright.sync_api import sync_playwright

            strategies = [
                self._strategy_iframe_content,
                self._strategy_direct_selectors,
                self._strategy_basic_wait,
            ]

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    page.goto(self.sheets_url, timeout=30000)

                    # Try each strategy until one succeeds
                    for strategy in strategies:
                        try:
                            html_content = strategy(page)
                            if self._validate_content(html_content):
                                return html_content
                        except Exception as e:
                            print(f"Strategy failed: {strategy.__name__}: {e}")
                            continue

                    # If all strategies fail, return basic content
                    return page.content()

                finally:
                    browser.close()

        def _strategy_iframe_content(self, page):
            """Strategy 1: Extract from iframe"""
            iframe_element = page.wait_for_selector(
                "iframe#pageswitcher-content", timeout=15000
            )
            iframe = iframe_element.content_frame()
            iframe.wait_for_selector("table td", timeout=15000)
            return iframe.content()

        def _strategy_direct_selectors(self, page):
            """Strategy 2: Direct selector waiting"""
            page.wait_for_selector("table td:not(:empty)", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=15000)
            return page.content()

        def _strategy_basic_wait(self, page):
            """Strategy 3: Basic timeout fallback"""
            page.wait_for_timeout(8000)
            return page.content()

        def _validate_content(self, html_content):
            """Validate that HTML contains actual table data"""
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, "html.parser")
            table = soup.find("table")
            if not table:
                return False

            # Check for actual data (more than just headers)
            rows = table.find_all("tr")
            return len(rows) > 1 and any(
                td.get_text(strip=True) for row in rows for td in row.find_all("td")
            )

    def _parse_html_table(self):
        """Enhanced parsing with schema awareness and structured data preservation"""

        html = GoogleSheetsRAG.LoadWebContent(self.sheets_url).load_web_content()
        if not html:
            raise ValueError(
                "Failed to load content from the provided Google Sheets URL."
            )
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            raise ValueError("No table found in the provided Google Sheets URL.")

        rows = table.find_all("tr")
        if not rows:
            return self.data

        # Extract headers from first row
        header_row = rows[0]
        header_cells = header_row.find_all(["th", "td"])
        self.headers = [cell.text.strip() for cell in header_cells if cell.text.strip()]

        # Process data rows
        for row in rows[1:]:  # Skip header row
            cols = row.find_all("td")
            if not cols:
                continue

            # Create structured row data
            row_data = {}
            cols_expanded = []

            for i, col in enumerate(cols):
                text = col.text.strip() if col.text else ""
                cols_expanded.append(text if text else None)

                # Map to headers if available
                if i < len(self.headers) and self.headers[i]:
                    row_data[self.headers[i]] = text if text else None

            # Remove trailing empty columns
            while cols_expanded and cols_expanded[-1] is None:
                cols_expanded.pop()

            if cols_expanded and any(cell is not None for cell in cols_expanded):
                self.data.append(cols_expanded)
                if row_data:
                    self.structured_data.append(row_data)

        return self.data

    def _generate_schema_description(self):
        """Generate schema description based on headers and config"""
        schema_desc = "SPREADSHEET SCHEMA:\n"
        schema_desc += f"Columns: {', '.join(self.headers)}\n"

        # Add schema configuration if provided
        if self.schema_config:
            schema_desc += "\nCOLUMN RELATIONSHIPS:\n"
            for config_key, config_value in self.schema_config.items():
                schema_desc += f"- {config_key}: {config_value}\n"

        # Add relationship extraction guidance
        schema_desc += "\nEXTRACTION GUIDANCE:\n"
        schema_desc += "- Each row represents a connected entity or record\n"
        schema_desc += (
            "- Look for relationships between column values within the same row\n"
        )
        schema_desc += (
            "- Consider hierarchical relationships (parent-child, category-item)\n"
        )
        schema_desc += "- Identify attribute relationships (entity-property-value)\n"

        return schema_desc

    def _create_row_context(self, row_data, row_index):
        """Create rich context for a single row"""
        context = f"Record #{row_index + 1}:\n"

        for header, value in row_data.items():
            if value:
                context += f"  {header}: {value}\n"

        # Add potential relationships hint
        non_empty_values = [f"{k}={v}" for k, v in row_data.items() if v]
        if len(non_empty_values) > 1:
            context += f"\nPotential relationships in this record: {' | '.join(non_empty_values)}\n"

        return context

    def get_structured_documents_for_kg(self):
        """
        Convert structured spreadsheet data into knowledge graph friendly format
        Returns documents with schema context for better triple extraction
        """
        from langchain_core.documents import Document

        if not self.structured_data:
            self._parse_html_table()

        documents = []

        # Create schema description
        schema_description = self._generate_schema_description()

        # Process each row with full context
        for i, row_data in enumerate(self.structured_data):
            # Create rich context for each row
            row_context = self._create_row_context(row_data, i)

            # Combine schema + row context
            full_content = f"{schema_description}\n\nROW DATA:\n{row_context}"

            documents.append(
                Document(
                    page_content=full_content,
                    metadata={
                        "row_index": i,
                        "data_type": "structured_spreadsheet",
                        "headers": self.headers,
                        "raw_data": row_data,
                    },
                )
            )

        return documents


#  def parse_html_table(self):
# #old way
#         # Fetch the HTML content of the Google Sheets page
#         response = requests.get(self.sheets_url)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, 'html.parser')
#         # Find the table in the HTML
#         table = soup.find('table')
#         if not table:
#             raise ValueError("No table found in the provided Google Sheets URL.")
#
#         # now append the rows to the data list
#         for row in table.find_all('tr'):
#             cols = row.find_all('td')
#             # Extract text from each cell in the row
#             cols_expanded = []
#             for col in cols[:-1]:  # Exclude the last one column
#                 text = col.text
#                 if text.strip() == '':
#                     # Remove leading/trailing whitespace and add to the list
#                     cols_expanded.append(None)
#                 else:
#                     cols_expanded.append(text)
#                 if cols_expanded[::] == [None] * len(cols_expanded):
#                 #if all(col is None for col in cols_expanded): # (we could also use this but only in python)
#                     # if all columns are None, then remove the last column
#                     cols_expanded.pop()
#
#             # cols = [ele.text.strip() for ele in cols]
#             if cols_expanded:
#                 # print(cols_expanded)
#                 # sleep(0.5)
#                 self.data.append(cols_expanded)
#
#         return self.data

if __name__ == "__main__":
    # working
    url = "https://docs.google.com/spreadsheets/d/1OOfUsC8sQmXNiHs2NQR03Tq6qVO5vJxrvLfeZAY0U4Q/edit?gid=0#gid=0"
    print(url.split("https://docs.google.com/spreadsheets/")[0].lower() == "")
    g = GoogleSheetsRAG(url)
    [
        print(f"{'-' * 50}\n{row}\n{'-' * 80}")
        for row in g.get_structured_documents_for_kg()[0:2]
    ]
    # ex = timeit.timeit(g.parse_html_table, number=100)
    # print(f"Execution time: {ex} seconds")
