import scrapy
from urllib.parse import urljoin

class DrugsSpider(scrapy.Spider):
    name = "drugs"
    allowed_domains = ["drugs.com"]
    start_urls = ["https://www.drugs.com/drug_information.html"]

    def parse(self, response):
        # Extract all main alphabetic links (A-Z)
        alpha_links = response.css('.ddc-paging > ul:nth-child(2) > li > a::attr(href)').getall()
        for link in alpha_links:
            yield response.follow(link, callback=self.parse_alpha)


    def parse_alpha(self, response):
        # Extract drugs under each alphabet sub-section (e.g., Aa, Ab, etc.)
        drug_sections = response.css('#content > ul > li > a::attr(href)').getall()
        for drug_link in drug_sections:
            full_drug_link = urljoin(response.url, drug_link)
            yield response.follow(full_drug_link, callback=self.parse_drug)

    def parse_drug(self, response):
        # Extract drug information
        drug_name = response.css('h1::text').get().strip()
        categories = response.css('#content > nav > ul > li > a::text').getall()
        category_links = response.css('#content > nav > ul > li > a::attr(href)').getall()

        # Combine category names with links
        related_links = [
            {"label": label.strip(), "link": urljoin(response.url, link)}
            for label, link in zip(categories, category_links)
        ]

        # Preprocess the text under each section
        sections = {}
        for section in categories:
            # Convert section name to lowercase and replace spaces with hyphens
            section_id = section.strip().lower().replace(" ", "-")
            # Scrape the data for this section
            section_data = response.css(f"#{section_id} ~ p::text").getall()
            sections[section] = " ".join([text.strip() for text in section_data])

        yield {
            "drug_name": drug_name,
            "sections": sections,
            "related_links": related_links,
        }
