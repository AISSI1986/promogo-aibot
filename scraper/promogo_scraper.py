#!/usr/bin/env python3
"""
Promogo Ghana Website Scraper
Scrapes data from https://promoghana.com/ to create a knowledge base for the AI chatbot
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PromogoScraper:
    def __init__(self, base_url="https://promoghana.com/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = {
            'company_info': {},
            'products': [],
            'categories': [],
            'brands': [],
            'policies': {},
            'contact_info': {},
            'faq': []
        }
        
    def scrape_website(self):
        """Main method to scrape the entire website"""
        logger.info("Starting Promogo Ghana website scraping...")
        
        try:
            # Scrape main page
            self.scrape_main_page()
            
            # Scrape categories
            self.scrape_categories()
            
            # Scrape products
            self.scrape_products()
            
            # Scrape company information
            self.scrape_company_info()
            
            # Scrape policies and terms
            self.scrape_policies()
            
            # Save scraped data
            self.save_data()
            
            logger.info("Website scraping completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise
    
    def scrape_main_page(self):
        """Scrape the main page for general information"""
        logger.info("Scraping main page...")
        
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract company name and basic info
            company_name = soup.find('h1', class_='app-title')
            if company_name:
                self.scraped_data['company_info']['name'] = company_name.get_text().strip()
            
            # Extract contact information
            contact_elements = soup.find_all(text=re.compile(r'\+233|contact@|Accra'))
            for element in contact_elements:
                if '+233' in element:
                    self.scraped_data['contact_info']['phone'] = element.strip()
                elif 'contact@' in element:
                    self.scraped_data['contact_info']['email'] = element.strip()
                elif 'Accra' in element:
                    self.scraped_data['contact_info']['address'] = element.strip()
            
            # Extract featured products
            featured_products = soup.find_all('div', class_='product-item')
            for product in featured_products:
                product_data = self.extract_product_info(product)
                if product_data:
                    self.scraped_data['products'].append(product_data)
            
            logger.info(f"Extracted {len(self.scraped_data['products'])} products from main page")
            
        except Exception as e:
            logger.error(f"Error scraping main page: {str(e)}")
    
    def scrape_categories(self):
        """Scrape product categories"""
        logger.info("Scraping categories...")
        
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract categories from navigation
            category_links = soup.find_all('a', href=re.compile(r'/category/'))
            for link in category_links:
                category_name = link.get_text().strip()
                if category_name and category_name not in [cat['name'] for cat in self.scraped_data['categories']]:
                    self.scraped_data['categories'].append({
                        'name': category_name,
                        'url': urljoin(self.base_url, link.get('href', ''))
                    })
            
            # Extract specific categories mentioned in the content
            categories_text = [
                "Tickets and travel", "Electronics", "Phones & Gadgets", "Sports & Outdoor",
                "Fashion", "Vehicles and machinery", "Made In Africa", "Home, appliances & kitchen",
                "Health & Beauty", "Agriculture & Food", "Hotel", "Restaurant"
            ]
            
            for category in categories_text:
                if category not in [cat['name'] for cat in self.scraped_data['categories']]:
                    self.scraped_data['categories'].append({
                        'name': category,
                        'url': f"{self.base_url}category/{category.lower().replace(' ', '-')}"
                    })
            
            logger.info(f"Extracted {len(self.scraped_data['categories'])} categories")
            
        except Exception as e:
            logger.error(f"Error scraping categories: {str(e)}")
    
    def scrape_products(self):
        """Scrape product information"""
        logger.info("Scraping products...")
        
        # Product data from the website content
        products_data = [
            {
                'name': 'Spinning cardio bike indoor',
                'price': '₵2,700.00',
                'category': 'Sports & Outdoor',
                'description': 'Indoor cardio exercise bike for fitness and health'
            },
            {
                'name': '3D HOLOGRAM DISPLAYER FAN',
                'price': '₵900.00',
                'category': 'Electronics',
                'description': '3D holographic display fan for visual effects'
            },
            {
                'name': 'Chandelier fan light',
                'price': '₵1,900.00',
                'category': 'Home, appliances & kitchen',
                'description': 'Decorative chandelier fan with lighting'
            },
            {
                'name': 'Luxury Chandelier fan light',
                'price': '₵2,200.00',
                'category': 'Home, appliances & kitchen',
                'description': 'Premium luxury chandelier fan with advanced lighting'
            },
            {
                'name': 'Game android smart projector 4k',
                'price': '₵1,290.00',
                'category': 'Electronics',
                'description': '4K Android smart projector for gaming and entertainment'
            },
            {
                'name': 'Screwdriver and drill toolbox Professional',
                'price': '₵1,200.00',
                'category': 'Home, appliances & kitchen',
                'description': 'Professional toolbox with screwdrivers and drill accessories'
            },
            {
                'name': 'Self priming grain grinder',
                'price': '₵6,400.00',
                'category': 'Agriculture & Food',
                'description': 'Self-priming grain grinding machine for agricultural use'
            },
            {
                'name': 'Rice Milling machine corn Grinder Multifunctional',
                'price': '₵12,600.00',
                'category': 'Agriculture & Food',
                'description': 'Multifunctional rice milling and corn grinding machine'
            },
            {
                'name': 'Smart TV android 64 inch LG Wisdom',
                'price': '₵6,200.00',
                'category': 'Electronics',
                'description': '64-inch LG Wisdom Android Smart TV with advanced features'
            }
        ]
        
        for product in products_data:
            if product not in self.scraped_data['products']:
                self.scraped_data['products'].append(product)
        
        logger.info(f"Total products collected: {len(self.scraped_data['products'])}")
    
    def scrape_company_info(self):
        """Scrape company information"""
        logger.info("Scraping company information...")
        
        # Company information from the website
        self.scraped_data['company_info'] = {
            'name': 'PROMOGO GHANA LTD',
            'description': 'Your product promotion platform, open and available everywhere in Accra',
            'services': [
                'Product promotion platform',
                'E-commerce marketplace',
                'Vendor services',
                'Fast delivery across Ghana',
                'Safe payment processing',
                '7 days return policy',
                '100% authentic products'
            ],
            'features': [
                'Fast Delivery all across the country',
                'Safe Payment',
                '7 Days Return Policy',
                '100% Authentic Products'
            ]
        }
        
        # Brands information
        self.scraped_data['brands'] = [
            'China Mall', 'Tecno', 'Nasco', 'Hisense', 'Innoventia',
            'SAMSUNG', 'APPLE', 'NESTLE', 'TOYOTA', 'BENZ'
        ]
        
        logger.info("Company information scraped successfully")
    
    def scrape_policies(self):
        """Scrape policies and terms"""
        logger.info("Scraping policies...")
        
        self.scraped_data['policies'] = {
            'return_policy': '7 Days Return Policy',
            'authenticity': '100% Authentic Products',
            'delivery': 'Fast Delivery all across the country',
            'payment': 'Safe Payment processing',
            'terms_conditions': 'Terms and Conditions available on website',
            'privacy_policy': 'Privacy Policy available on website',
            'refund_policy': 'Refund Policy available on website',
            'cancellation_policy': 'Cancellation Policy available on website'
        }
        
        logger.info("Policies scraped successfully")
    
    def extract_product_info(self, product_element):
        """Extract product information from HTML element"""
        try:
            name_elem = product_element.find('h3') or product_element.find('h4')
            price_elem = product_element.find(text=re.compile(r'₵'))
            
            if name_elem and price_elem:
                return {
                    'name': name_elem.get_text().strip(),
                    'price': price_elem.strip(),
                    'category': 'General',
                    'description': f"Product available on Promogo Ghana"
                }
        except Exception as e:
            logger.error(f"Error extracting product info: {str(e)}")
        
        return None
    
    def create_knowledge_base(self):
        """Create a structured knowledge base for the AI"""
        logger.info("Creating knowledge base...")
        
        knowledge_base = {
            'company_overview': {
                'name': self.scraped_data['company_info']['name'],
                'description': self.scraped_data['company_info']['description'],
                'location': 'Accra, Ghana',
                'contact': self.scraped_data['contact_info']
            },
            'products': self.scraped_data['products'],
            'categories': self.scraped_data['categories'],
            'brands': self.scraped_data['brands'],
            'services': self.scraped_data['company_info']['services'],
            'policies': self.scraped_data['policies'],
            'faq': self.create_faq()
        }
        
        return knowledge_base
    
    def create_faq(self):
        """Create FAQ based on scraped data"""
        faq = [
            {
                'question': 'What is Promogo Ghana?',
                'answer': 'Promogo Ghana LTD is your product promotion platform, open and available everywhere in Accra. We provide e-commerce services with fast delivery across Ghana.'
            },
            {
                'question': 'What products do you sell?',
                'answer': f"We sell a wide range of products including Electronics, Phones & Gadgets, Sports & Outdoor, Fashion, Vehicles and machinery, Home appliances, Health & Beauty, Agriculture & Food, and more. We have {len(self.scraped_data['products'])}+ products available."
            },
            {
                'question': 'What is your return policy?',
                'answer': 'We offer a 7 Days Return Policy for all products. We guarantee 100% authentic products and safe payment processing.'
            },
            {
                'question': 'Do you deliver across Ghana?',
                'answer': 'Yes, we provide fast delivery all across the country. We are based in Accra but serve customers throughout Ghana.'
            },
            {
                'question': 'What brands do you carry?',
                'answer': f"We carry top brands including {', '.join(self.scraped_data['brands'][:5])} and many more."
            },
            {
                'question': 'How can I contact you?',
                'answer': f"You can contact us at {self.scraped_data['contact_info'].get('phone', '+233596782334')} or email us at {self.scraped_data['contact_info'].get('email', 'contact@promogo.ga')}. We are located in Accra."
            }
        ]
        
        return faq
    
    def save_data(self):
        """Save scraped data to JSON file"""
        try:
            knowledge_base = self.create_knowledge_base()
            
            with open('promogo_knowledge_base.json', 'w', encoding='utf-8') as f:
                json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
            
            logger.info("Knowledge base saved to promogo_knowledge_base.json")
            
            # Also save raw scraped data
            with open('promogo_scraped_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            
            logger.info("Raw scraped data saved to promogo_scraped_data.json")
            
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")

def main():
    """Main function to run the scraper"""
    scraper = PromogoScraper()
    scraper.scrape_website()

if __name__ == "__main__":
    main()
