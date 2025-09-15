"""
NCBI E-utilities service for retrieving scientific literature and database information.
Uses the free NCBI API to search PubMed and other databases.
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import time

class NCBIService:
    """Service for interacting with NCBI databases via E-utilities."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    def __init__(self, email: str = "bioquery@example.com", tool: str = "bioquery-assistant"):
        """Initialize NCBI service with contact information."""
        self.email = email
        self.tool = tool
        self.rate_limit_delay = 0.34  # ~3 requests per second for free tier
        
    def search_pubmed(self, query: str, max_results: int = 5, sort: str = "relevance") -> List[Dict]:
        """
        Search PubMed for articles matching the query.
        
        Args:
            query: Search terms
            max_results: Maximum number of results to return
            sort: Sort order ('relevance', 'pub_date', 'author')
            
        Returns:
            List of article dictionaries with title, authors, abstract, etc.
        """
        try:
            # Step 1: Search for PMIDs
            search_url = f"{self.BASE_URL}esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "sort": sort,
                "email": self.email,
                "tool": self.tool
            }
            
            response = requests.get(search_url, params=search_params)
            response.raise_for_status()
            
            # Parse XML response to get PMIDs
            root = ET.fromstring(response.content)
            pmids = [id_elem.text for id_elem in root.findall(".//Id")]
            
            if not pmids:
                return []
            
            time.sleep(self.rate_limit_delay)
            
            # Step 2: Fetch article details
            return self._fetch_article_details(pmids)
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    def _fetch_article_details(self, pmids: List[str]) -> List[Dict]:
        """Fetch detailed information for a list of PMIDs."""
        fetch_url = f"{self.BASE_URL}efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "email": self.email,
            "tool": self.tool
        }
        
        response = requests.get(fetch_url, params=fetch_params)
        response.raise_for_status()
        
        articles = []
        root = ET.fromstring(response.content)
        
        for article_elem in root.findall(".//PubmedArticle"):
            article_data = self._parse_article(article_elem)
            if article_data:
                articles.append(article_data)
        
        return articles
    
    def _parse_article(self, article_elem) -> Optional[Dict]:
        """Parse a single article XML element into a dictionary."""
        try:
            # Extract basic information
            article = article_elem.find(".//Article")
            if article is None:
                return None
            
            # Get PMID
            pmid_elem = article_elem.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else "Unknown"
            
            # Get title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "No title available"
            
            # Get authors
            authors = []
            for author_elem in article.findall(".//Author"):
                last_name = author_elem.find(".//LastName")
                first_name = author_elem.find(".//ForeName")
                if last_name is not None:
                    author_name = last_name.text
                    if first_name is not None:
                        author_name += f", {first_name.text}"
                    authors.append(author_name)
            
            # Get abstract
            abstract_elem = article.find(".//Abstract/AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
            
            # Get publication year
            pub_date = article.find(".//PubDate/Year")
            year = pub_date.text if pub_date is not None else "Unknown"
            
            # Get journal
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else "Unknown journal"
            
            return {
                "pmid": pmid,
                "title": title,
                "authors": authors[:3],  # Limit to first 3 authors
                "abstract": abstract[:500] + "..." if len(abstract) > 500 else abstract,
                "year": year,
                "journal": journal,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }
            
        except Exception as e:
            print(f"Error parsing article: {e}")
            return None
    
    def get_recent_papers(self, topic: str, max_results: int = 3) -> List[Dict]:
        """Get recent papers on a specific topic (last 2 years)."""
        # Add date filter for recent papers
        query = f"{topic} AND (\"2023\"[Date - Publication] OR \"2024\"[Date - Publication] OR \"2025\"[Date - Publication])"
        return self.search_pubmed(query, max_results, sort="pub_date")
    
    def format_articles_for_llm(self, articles: List[Dict]) -> str:
        """Format articles in a way that's useful for LLM context."""
        if not articles:
            return "No relevant articles found."
        
        formatted = "Recent relevant research:\n\n"
        for i, article in enumerate(articles, 1):
            authors_str = ", ".join(article["authors"])
            if len(article["authors"]) == 3:
                authors_str += " et al."
            
            formatted += f"{i}. **{article['title']}**\n"
            formatted += f"   Authors: {authors_str} ({article['year']})\n"
            formatted += f"   Journal: {article['journal']}\n"
            formatted += f"   Abstract: {article['abstract']}\n"
            formatted += f"   URL: {article['url']}\n\n"
        
        return formatted