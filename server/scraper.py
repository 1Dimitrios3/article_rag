import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin

class Scraper:
    def __init__(self):
        self._tracking_domains = [
            "scorecardresearch.com",
            "doubleclick.net",
            "googletagmanager.com",
            "adsystem.google.com",
            "analytics",
        ]

    def _is_tracking_image(self, image_url: str) -> bool:
        return any(domain in image_url for domain in self._tracking_domains)

    def _scrape_image(self, url: str):
        """
        Attempts to scrape the primary non-tracking image from the article and save it.
        The function iterates over all images, and if available, uses the width and height 
        attributes as a heuristic (area = width * height) to choose the largest one.
        The image is saved as "articleImage.png" inside the /images folder.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            candidates = []
            for img_tag in soup.find_all('img'):
                src = img_tag.get('src')
                if src and not self._is_tracking_image(src):
                    # Skip data URLs.
                    if src.startswith("data:"):
                        continue
                    
                    image_url = src
                    if not image_url.startswith(('http://', 'https://')):
                        image_url = urljoin(url, image_url)
                        
                    # Attempt to get the image dimensions from attributes.
                    width = img_tag.get('width')
                    height = img_tag.get('height')
                    area = 0
                    try:
                        if width and height:
                            area = int(width) * int(height)
                    except Exception:
                        area = 0  # If conversion fails, default to 0.
                    
                    candidates.append((image_url, area))
            
            if candidates:
                # Select the candidate with the maximum area.
                best_candidate = max(candidates, key=lambda x: x[1])
                best_image_url = best_candidate[0]
                
                # Save the image as articleImage.png in the /images folder.
                image_folder = os.path.join(os.getcwd(), 'images')
                os.makedirs(image_folder, exist_ok=True)
                image_filename = os.path.join(image_folder, "articleImage.png")
                
                img_response = requests.get(best_image_url, stream=True)
                img_response.raise_for_status()
                with open(image_filename, 'wb') as f:
                    for chunk in img_response.iter_content(1024):
                        f.write(chunk)
                print(f"Image saved as {image_filename}")
                return  # Stop after saving the best candidate.
            else:
                print("No suitable non-tracking image found.")
        except requests.RequestException as e:
            print(f"Image scraping failed: {e}")


    def _scrape_text(self, url: str):
        """
        Scrapes the article title and text snippets from the given URL.
        
        Returns:
            tuple: (title, text_snippets)
                title (str): The scraped <h1> title if available, otherwise the <title> text.
                text_snippets (List[str]): A list of all stripped text strings from the article.
        
        Raises:
            Exception: If the text scraping fails.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title: Prefer <h1>, fall back to <title> tag.
            title_tag = soup.find('h1')
            if title_tag and title_tag.get_text(strip=True):
                title = title_tag.get_text(strip=True)
            elif soup.title:
                title = soup.title.get_text(strip=True)
            else:
                title = ""
            
            # Extract text snippets.
            text_snippets = list(soup.stripped_strings)
            if not text_snippets:
                raise ValueError("No text content found.")
            
            return title, text_snippets
        except Exception as e:
            raise Exception(f"Text scraping failed: {e}")


    def scrape_article(self, url: str):
        """
        Public method: Scrapes both the image (optional) and text (required) from the article.
        Returns a dictionary with the article title and the full text (joined text snippets).
        """
        print("Starting image scraping...")
        self._scrape_image(url)
        
        print("Scraping text...")
        title, text_snippets = self._scrape_text(url)
        
        # Join the text snippets into one full text.
        article_text = " ".join(text_snippets) if isinstance(text_snippets, list) else text_snippets
        
        print("Scraping complete.")
        return {
            "title": title,
            "article_text": article_text
        }
