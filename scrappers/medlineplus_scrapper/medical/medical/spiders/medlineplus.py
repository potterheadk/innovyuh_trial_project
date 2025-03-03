import scrapy


class MedlinePlusSpider(scrapy.Spider):
    name = "medlineplus"
    allowed_domains = ["medlineplus.gov"]
    start_urls = ["https://medlineplus.gov/all_healthtopics.html"]

    def parse(self, response):
        """
        Parse the main A-Z page to extract links for each topic.
        """
        # Loop through each alphabetical section
        for a_tag in response.css("#topic_all > article > a"):
            section_id = a_tag.css("::attr(name)").get()
            if section_id:
                ul_selector = f"#section_{section_id} > ul > li"
                for li in response.css(ul_selector):
                    topic_name = li.css("a::text").get() or li.css("::text").get()
                    topic_url = li.css("a::attr(href)").get()

                    if topic_url:
                        # Follow the hyperlink to scrape detailed content
                        yield response.follow(
                            topic_url,
                            self.parse_topic,
                            meta={"topic_name": topic_name.strip()},
                        )
                    else:
                        # For topics without links, just record the name
                        yield {
                            "topic_name": topic_name.strip(),
                            "url": None,
                            "content": "No link available",
                            "other_links": []
                        }

    def parse_topic(self, response):
        """
        Parse individual topic pages to extract detailed content and other hyperlinks.
        """
        topic_name = response.meta["topic_name"]

        # Extract and preprocess the article content
        raw_content = response.css("#topic > article").get()
        if raw_content:
            processed_content = self.preprocess_content(raw_content)
        else:
            processed_content = "Content not found."

        # Extract other hyperlinks in the article section
        other_links = [
            {
                "text": link.css("::text").get().strip(),
                "url": link.css("::attr(href)").get()
            }
            for link in response.css("#topic > article a")
            if link.css("::attr(href)").get()  # Only include valid links
        ]

        yield {
            "topic_name": topic_name,
            "url": response.url,
            "content": processed_content,
            "other_links": other_links,
        }

    def preprocess_content(self, raw_html):
        """
        Preprocess the raw HTML content to remove unnecessary tags, whitespace, and format nicely.
        """
        from w3lib.html import remove_tags, replace_escape_chars

        # Remove all HTML tags
        text_content = remove_tags(raw_html)

        # Replace HTML escape characters (e.g., &nbsp;, &amp;)
        text_content = replace_escape_chars(text_content)

        # Remove extra spaces and newlines
        text_content = " ".join(text_content.split())

        return text_content
