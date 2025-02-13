import requests
from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import time
import random

def make_request(url, max_retries=3, delay=2):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }

    for attempt in range(max_retries):
        try:
            # Ajouter un délai aléatoire entre les requêtes
            time.sleep(delay + random.uniform(0, 2))
            
            response = requests.get(
                url, 
                headers=headers,
                timeout=10,
                verify=True
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:  # Dernière tentative
                raise e
            time.sleep(delay * (attempt + 1))  # Délai croissant entre les tentatives
            continue

def scrape_zataz_section(url, section_type):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        if section_type in ['cybersecurity', 'darkweb']:
            # Pour la section cybersécurité ou darknet
            items = soup.find_all('div', class_='blog-context-wrapper')
            for item in items:
                titre_element = item.find('h2', class_='blog-title')
                if titre_element and titre_element.find('a'):
                    lien_element = titre_element.find('a')
                    titre = lien_element.text.strip()
                    lien = lien_element['href']
                else:
                    titre = "Titre non disponible"
                    lien = "#"
                
                contenu_element = item.find('div', class_='blog-content')
                contenu = contenu_element.text.strip() if contenu_element else "Contenu non disponible"
                articles.append({'titre': titre, 'lien': lien, 'contenu': contenu, 'category': section_type})

        elif section_type == 'osint':
            # Pour la section OSINT avec gestion des iframes
            iframes = soup.find_all('iframe', class_='wp-embedded-content')
            for iframe in iframes:
                # Récupérer l'URL source de l'iframe
                src = iframe.get('src', '')
                if src:
                    try:
                        # Récupérer le contenu de l'iframe
                        article_response = requests.get(src)
                        article_response.raise_for_status()
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        
                        # Trouver le div principal de l'article dans l'iframe
                        article_div = article_soup.find('div', class_=lambda x: x and 'wp-embed post-' in x)
                        if article_div:
                            # Récupérer le titre et le lien depuis wp-embed-heading
                            heading = article_div.find('p', class_='wp-embed-heading')
                            if heading and heading.find('a'):
                                lien_element = heading.find('a')
                                titre = lien_element.text.strip()
                                # Enlever '/embed/' de l'URL
                                lien = lien_element['href'].replace('/embed/', '/')
                            else:
                                titre = "Titre non disponible"
                                lien = "#"
                            
                            # Récupérer le contenu depuis wp-embed-excerpt
                            excerpt = article_div.find('div', class_='wp-embed-excerpt')
                            if excerpt and excerpt.find('p'):
                                contenu = excerpt.find('p').text.strip()
                            else:
                                contenu = "Contenu non disponible"
                            
                            articles.append({
                                'titre': titre,
                                'lien': lien,
                                'contenu': contenu,
                                'category': 'osint'
                            })
                    except Exception as e:
                        print(f"Erreur lors de la récupération de l'article {src}: {str(e)}")
                        continue

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping de {section_type}: {str(e)}")
        return []

def scrape_itconnect_courses(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles de cours
        course_articles = soup.find_all('article', class_='sfwd-courses')
        
        if course_articles:
            for article in course_articles:
                # Extraire le titre et le lien depuis h2.cm-entry-title > a
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image depuis div.cm-featured-image > a > img
                featured_image = article.find('div', class_='cm-featured-image')
                if featured_image and featured_image.find('img'):
                    img = featured_image.find('img')
                    # Gérer les images avec lazy loading
                    image_url = img.get('data-lazy-src', img.get('src', ''))
                    image_alt = img.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire le nombre de chapitres
                chapters_element = article.find('div', class_='course-informations__steps-count')
                chapters = chapters_element.text.strip() if chapters_element else ""

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'chapters': chapters,
                    'category': 'courses'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des cours IT-Connect: {str(e)}")
        return []

def scrape_itconnect_sysadmin(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'category': 'sysadmin'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des articles SysAdmin: {str(e)}")
        return []

def scrape_itconnect_netadmin(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                # Extraire la catégorie
                category_element = article.find('div', class_='cm-post-categories')
                if category_element and category_element.find('a'):
                    category = category_element.find('a').text.strip()
                else:
                    category = "Non catégorisé"

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'subcategory': category,
                    'category': 'netadmin'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des articles NetAdmin: {str(e)}")
        return []

def scrape_itconnect_cybersec(url):
    try:
        response = make_request(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                # Extraire les tags
                tags = []
                tags_element = article.find('span', class_='cm-tag-links')
                if tags_element and tags_element.find_all('a'):
                    tags = [tag.text.strip() for tag in tags_element.find_all('a')]

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'tags': tags,
                    'category': 'cybersec'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des articles Cybersécurité: {str(e)}")
        return []

def scrape_itconnect_cybernews(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                # Extraire la date
                date_element = article.find('span', class_='cm-post-date').find('time')
                date = date_element.text.strip() if date_element else ""

                # Extraire l'auteur
                author_element = article.find('span', class_='cm-author').find('a')
                author = author_element.text.strip() if author_element else ""

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'date': date,
                    'author': author,
                    'category': 'cybernews'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des actualités Cybersécurité: {str(e)}")
        return []

def scrape_itconnect_webnews(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                # Extraire la date
                date_element = article.find('span', class_='cm-post-date').find('time')
                date = date_element.text.strip() if date_element else ""

                # Extraire l'auteur
                author_element = article.find('span', class_='cm-author').find('a')
                author = author_element.text.strip() if author_element else ""

                # Extraire les commentaires
                comments_element = article.find('span', class_='cm-comments-link').find('a')
                comments = comments_element.text.strip() if comments_element else "0 commentaire"

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'date': date,
                    'author': author,
                    'comments': comments,
                    'category': 'webnews'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des actualités Web: {str(e)}")
        return []

def scrape_itconnect_osnews(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                # Extraire la date
                date_element = article.find('span', class_='cm-post-date').find('time')
                date = date_element.text.strip() if date_element else ""

                # Extraire l'auteur
                author_element = article.find('span', class_='cm-author').find('a')
                author = author_element.text.strip() if author_element else ""

                # Extraire les tags
                tags = []
                tags_element = article.find('span', class_='cm-tag-links')
                if tags_element and tags_element.find_all('a'):
                    tags = [tag.text.strip() for tag in tags_element.find_all('a')]

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'date': date,
                    'author': author,
                    'tags': tags,
                    'category': 'osnews'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des actualités OS: {str(e)}")
        return []

def scrape_itconnect_hardnews(url):
    try:
        # Ajout des headers pour simuler un navigateur
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        }
        
        # Ajout des headers à la requête
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                # Extraire la date
                date_element = article.find('span', class_='cm-post-date').find('time')
                date = date_element.text.strip() if date_element else ""

                # Extraire l'auteur
                author_element = article.find('span', class_='cm-author').find('a')
                author = author_element.text.strip() if author_element else ""

                # Extraire les commentaires
                comments_element = article.find('span', class_='cm-comments-link').find('a')
                comments = comments_element.text.strip() if comments_element else "0 commentaire"

                # Extraire les tags
                tags = []
                tags_element = article.find('span', class_='cm-tag-links')
                if tags_element and tags_element.find_all('a'):
                    tags = [tag.text.strip() for tag in tags_element.find_all('a')]

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'date': date,
                    'author': author,
                    'comments': comments,
                    'tags': tags,
                    'category': 'hardnews'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des actualités Hardware: {str(e)}")
        return []

def scrape_itconnect_mobilenews(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                # Extraire la date
                date_element = article.find('span', class_='cm-post-date').find('time')
                date = date_element.text.strip() if date_element else ""

                # Extraire l'auteur
                author_element = article.find('span', class_='cm-author').find('a')
                author = author_element.text.strip() if author_element else ""

                # Extraire les commentaires
                comments_element = article.find('span', class_='cm-comments-link').find('a')
                comments = comments_element.text.strip() if comments_element else "0 commentaire"

                # Extraire les catégories
                categories = []
                categories_element = article.find('div', class_='cm-post-categories')
                if categories_element and categories_element.find_all('a'):
                    categories = [cat.text.strip() for cat in categories_element.find_all('a')]

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'date': date,
                    'author': author,
                    'comments': comments,
                    'categories': categories,
                    'category': 'mobilenews'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des actualités Mobile: {str(e)}")
        return []

def scrape_itconnect_deals(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Trouver tous les articles
        article_elements = soup.find_all('article', class_='post')
        
        if article_elements:
            for article in article_elements:
                # Extraire le titre et le lien
                titre_element = article.find('h2', class_='cm-entry-title').find('a')
                if titre_element:
                    titre = titre_element.text.strip()
                    lien = titre_element['href']
                else:
                    continue

                # Extraire l'image
                image_element = article.find('div', class_='cm-featured-image').find('img')
                if image_element:
                    image_url = image_element.get('data-lazy-src', image_element.get('src', ''))
                    image_alt = image_element.get('alt', '')
                else:
                    image_url = ""
                    image_alt = ""

                # Extraire la description
                description_element = article.find('div', class_='cm-entry-summary').find('p')
                description = description_element.text.strip() if description_element else ""

                # Extraire la date
                date_element = article.find('span', class_='cm-post-date').find('time')
                date = date_element.text.strip() if date_element else ""

                # Extraire l'auteur
                author_element = article.find('span', class_='cm-author').find('a')
                author = author_element.text.strip() if author_element else ""

                # Extraire les commentaires
                comments_element = article.find('span', class_='cm-comments-link').find('a')
                comments = comments_element.text.strip() if comments_element else "0 commentaire"

                # Extraire les tags
                tags = []
                tags_element = article.find('span', class_='cm-tag-links')
                if tags_element and tags_element.find_all('a'):
                    tags = [tag.text.strip() for tag in tags_element.find_all('a')]

                articles.append({
                    'titre': titre,
                    'lien': lien,
                    'image_url': image_url,
                    'image_alt': image_alt,
                    'description': description,
                    'date': date,
                    'author': author,
                    'comments': comments,
                    'tags': tags,
                    'category': 'deals'
                })

        return articles
    except Exception as e:
        print(f"Erreur lors du scraping des bons plans: {str(e)}")
        return []

def scrape_youtube_channel_simple(url):
    try:
        response = make_request(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Récupérer les informations de base de la chaîne
        channel_info = {
            'title': 'IT-Connect',
            'url': url,
            'thumbnail': 'https://yt3.googleusercontent.com/ytc/AIf8zZTDkajQxPa4sjDOVp9FXSr_c3-KZP4oHqOjnNZE=s176-c-k-c0x00ffffff-no-rj',  # Image de profil IT-Connect
            'description': 'Chaîne officielle IT-Connect - Tutoriels et actualités informatiques'
        }
        
        return channel_info
    except Exception as e:
        print(f"Erreur lors du scraping de la chaîne YouTube: {str(e)}")
        return None

def scrape_zataz(output_title=None):
    try:
        # Gestion du nom du fichier de sortie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_title:
            output_file = f'{output_title}.html'
        else:
            output_file = f'articles_{timestamp}.html'

        # Obtenir la date actuelle au format français
        current_time = datetime.now().strftime("%d/%m/%Y")

        # Template HTML avec le nouveau design
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Veille Technologique</title>
            <meta charset="UTF-8">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f7fa;
                    color: #2d3436;
                    line-height: 1.6;
                }

                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 2rem;
                }

                h1 {
                    font-size: 2.5rem;
                    color: #2d3436;
                    margin-bottom: 2rem;
                    text-align: center;
                    font-weight: 600;
                }

                .tab {
                    background: white;
                    padding: 1rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                    margin-bottom: 2rem;
                    display: flex;
                    gap: 1rem;
                    overflow-x: auto;
                    position: sticky;
                    top: 1rem;
                    z-index: 1000;
                }

                .tab button {
                    background: transparent;
                    border: none;
                    padding: 0.8rem 1.5rem;
                    border-radius: 8px;
                    font-size: 1rem;
                    font-weight: 500;
                    color: #636e72;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    white-space: nowrap;
                }

                .tab button:hover {
                    background: #f1f2f6;
                    color: #2d3436;
                }

                .tab button.active {
                    background: #00b894;
                    color: white;
                }

                .content {
                    display: none;
                    animation: fadeIn 0.5s ease;
                }

                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                .content.active {
                    display: block;
                }

                .subcategories {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.8rem;
                    margin-bottom: 2rem;
                    padding: 1rem;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                }

                .subcategory {
                    padding: 0.6rem 1.2rem;
                    border: none;
                    border-radius: 6px;
                    background: #f1f2f6;
                    color: #636e72;
                    cursor: pointer;
                    font-size: 0.9rem;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }

                .subcategory:hover {
                    background: #dfe6e9;
                    color: #2d3436;
                }

                .subcategory.active {
                    background: #00b894;
                    color: white;
                }

                .articles-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 2rem;
                    padding: 1rem;
                }

                .article {
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                    transition: all 0.3s ease;
                }

                .article:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1);
                }

                .article-image {
                    position: relative;
                    overflow: hidden;
                    aspect-ratio: 16/9;
                }

                .article-image img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    transition: transform 0.3s ease;
                }

                .article:hover .article-image img {
                    transform: scale(1.05);
                }

                .article-meta {
                    padding: 1rem;
                    display: flex;
                    gap: 1rem;
                    font-size: 0.9rem;
                    color: #636e72;
                    border-bottom: 1px solid #f1f2f6;
                }

                .titre {
                    padding: 1rem;
                    font-size: 1.2rem;
                    color: #2d3436;
                    margin: 0;
                    line-height: 1.4;
                }

                .description {
                    padding: 0 1rem;
                    color: #636e72;
                    font-size: 0.95rem;
                    margin-bottom: 1rem;
                }

                .tags, .categories {
                    padding: 0 1rem;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                    margin-bottom: 1rem;
                }

                .tag, .category-tag, .deal-tag {
                    padding: 0.4rem 0.8rem;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    font-weight: 500;
                }

                .tag {
                    background: #74b9ff;
                    color: white;
                }

                .category-tag {
                    background: #a29bfe;
                    color: white;
                }

                .deal-tag {
                    background: #00b894;
                    color: white;
                }

                .lien {
                    display: block;
                    padding: 1rem;
                    text-align: center;
                    background: #00b894;
                    color: white;
                    text-decoration: none;
                    font-weight: 500;
                    transition: background 0.3s ease;
                }

                .lien:hover {
                    background: #00a884;
                }

                .chapters {
                    padding: 0.5rem 1rem;
                    color: #636e72;
                    font-size: 0.9rem;
                    background: #f1f2f6;
                    margin: 0 1rem 1rem;
                    border-radius: 4px;
                }
            </style>
            <script>
            function openTab(evt, tabName) {
                var i, content, tablinks;
                content = document.getElementsByClassName("content");
                for (i = 0; i < content.length; i++) {
                    content[i].style.display = "none";
                }
                tablinks = document.getElementsByClassName("tablinks");
                for (i = 0; i < tablinks.length; i++) {
                    tablinks[i].className = tablinks[i].className.replace(" active", "");
                }
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }

            function filterCategory(category, button) {
                var articles = document.getElementsByClassName("article");
                var buttons = button.parentElement.getElementsByClassName("subcategory");
                
                for (var i = 0; i < buttons.length; i++) {
                    buttons[i].classList.remove("active");
                }
                button.classList.add("active");
                
                for (var i = 0; i < articles.length; i++) {
                    if (category === "all" || articles[i].getAttribute("data-category") === category) {
                        articles[i].style.display = "block";
                    } else {
                        articles[i].style.display = "none";
                    }
                }
            }

            // Activer le premier onglet par défaut
            document.addEventListener("DOMContentLoaded", function() {
                document.querySelector(".tablinks").click();
            });
            </script>
        </head>
        <body>
            <div class="container">
                <h1>Veille Technologique</h1>
                
                <div class="tab">
                    <button class="tablinks active" onclick="openTab(event, 'zataz')">ZATAZ</button>
                    <button class="tablinks" onclick="openTab(event, 'itconnect')">IT Connect</button>
                    <button class="tablinks" onclick="openTab(event, 'youtube')">Chaînes Youtube</button>
                </div>

                <div id="zataz" class="content active">
                    <div class="subcategories">
                        <button class="subcategory active" onclick="filterCategory('all', this)">Tous</button>
                        <button class="subcategory" onclick="filterCategory('cybersecurity', this)">Cybersécurité</button>
                        <button class="subcategory" onclick="filterCategory('darkweb', this)">Dark Web</button>
                        <button class="subcategory" onclick="filterCategory('osint', this)">OSINT</button>
                    </div>
                    <div class="articles-grid">"""

        # Scraping des différentes sections
        cybersecurity_articles = scrape_zataz_section('https://www.zataz.com/category/secu/', 'cybersecurity')
        darkweb_articles = scrape_zataz_section('https://www.zataz.com/category/actualites/internet-clandestin-darknet/', 'darkweb')
        osint_articles = scrape_zataz_section('https://www.zataz.com/osint/', 'osint')
        
        # Scraping IT-Connect
        itconnect_courses = scrape_itconnect_courses('https://www.it-connect.fr/cours-it-gratuits/')
        sysadmin_articles = scrape_itconnect_sysadmin('https://www.it-connect.fr/cours-tutoriels/administration-systemes/')
        netadmin_articles = scrape_itconnect_netadmin('https://www.it-connect.fr/cours-tutoriels/administration-reseau/')
        cybersec_articles = scrape_itconnect_cybersec('https://www.it-connect.fr/cours-tutoriels/securite-informatique/')
        cybernews_articles = scrape_itconnect_cybernews('https://www.it-connect.fr/actualites/actu-securite/')
        webnews_articles = scrape_itconnect_webnews('https://www.it-connect.fr/actualites/actu-internet/')
        osnews_articles = scrape_itconnect_osnews('https://www.it-connect.fr/actualites/actu-logiciel-os/')
        hardnews_articles = scrape_itconnect_hardnews('https://www.it-connect.fr/actualites/actu-materiel/')
        mobilenews_articles = scrape_itconnect_mobilenews('https://www.it-connect.fr/actualites/actu-mobile/')
        deals_articles = scrape_itconnect_deals('https://www.it-connect.fr/bons-plans-high-tech/')

        # Ajout des articles Zataz
        for article in cybersecurity_articles + darkweb_articles + osint_articles:
            html_content += f"""
                <div class="article" data-category="{article['category']}">
                    <div class="article-content">
                        <div class="article-category">{article['category'].upper()}</div>
                        <h2 class="titre">{article['titre']}</h2>
                        <p class="description">{article['contenu'][:200]}...</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'article</a>
                    </div>
                </div>"""

        # Fermeture de la section Zataz
        html_content += """
            </div>
        </div>"""

        # Partie IT-Connect
        html_content += """
        <div id="itconnect" class="content">
            <div class="subcategories">
                <button class="subcategory active" onclick="filterCategory('all', this)">Tous</button>
                <button class="subcategory" onclick="filterCategory('courses', this)">Cours IT</button>
                <button class="subcategory" onclick="filterCategory('sysadmin', this)">Cours SysAdmin</button>
                <button class="subcategory" onclick="filterCategory('netadmin', this)">Cours NetAdmin</button>
                <button class="subcategory" onclick="filterCategory('cybersec', this)">Cours Cybersécurité</button>
                <button class="subcategory" onclick="filterCategory('cybernews', this)">Actu Cybersécurité</button>
                <button class="subcategory" onclick="filterCategory('webnews', this)">Actu Web</button>
                <button class="subcategory" onclick="filterCategory('osnews', this)">Actu OS</button>
                <button class="subcategory" onclick="filterCategory('hardnews', this)">Actu Hardware</button>
                <button class="subcategory" onclick="filterCategory('mobilenews', this)">Actu Mobile</button>
                <button class="subcategory" onclick="filterCategory('deals', this)">Bons Plans Tech</button>
            </div>
            <div class="articles-grid">"""

        # Ajout des articles IT-Connect
        if itconnect_courses:  # Vérifie si des cours ont été trouvés
            for article in itconnect_courses:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <div class="chapters">{article['chapters']}</div>
                        <a href="{article['lien']}" class="lien" target="_blank">Voir le cours</a>
                    </div>"""

        # Ajout des articles SysAdmin
        if sysadmin_articles:  # Vérifie si des articles ont été trouvés
            for article in sysadmin_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'article</a>
                    </div>"""

        # Ajout des articles NetAdmin
        if netadmin_articles:  # Vérifie si des articles ont été trouvés
            for article in netadmin_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <div class="subcategory-tag">{article['subcategory']}</div>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'article</a>
                    </div>"""

        # Ajout des articles Cybersécurité
        if cybersec_articles:  # Vérifie si des articles ont été trouvés
            for article in cybersec_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <div class="tags">
                            {' '.join([f'<span class="tag">{tag}</span>' for tag in article['tags']])}
                        </div>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'article</a>
                    </div>"""

        # Ajout des actualités Cybersécurité
        if cybernews_articles:
            for article in cybernews_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <div class="article-meta">
                            <span class="date">{article['date']}</span>
                            <span class="author">Par {article['author']}</span>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'actualité</a>
                    </div>"""

        # Ajout des actualités Web
        if webnews_articles:
            for article in webnews_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <div class="article-meta">
                            <span class="date">{article['date']}</span>
                            <span class="author">Par {article['author']}</span>
                            <span class="comments">{article['comments']}</span>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'actualité</a>
                    </div>"""

        # Ajout des actualités OS
        if osnews_articles:
            for article in osnews_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <div class="article-meta">
                            <span class="date">{article['date']}</span>
                            <span class="author">Par {article['author']}</span>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <div class="tags">
                            {' '.join([f'<span class="tag">{tag}</span>' for tag in article['tags']])}
                        </div>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'actualité</a>
                    </div>"""

        # Ajout des actualités Hardware
        if hardnews_articles:
            for article in hardnews_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <div class="article-meta">
                            <span class="date">{article['date']}</span>
                            <span class="author">Par {article['author']}</span>
                            <span class="comments">{article['comments']}</span>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <div class="tags">
                            {' '.join([f'<span class="tag">{tag}</span>' for tag in article['tags']])}
                        </div>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'actualité</a>
                    </div>"""

        # Ajout des actualités Mobile
        if mobilenews_articles:
            for article in mobilenews_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <div class="article-meta">
                            <span class="date">{article['date']}</span>
                            <span class="author">Par {article['author']}</span>
                            <span class="comments">{article['comments']}</span>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <div class="categories">
                            {' '.join([f'<span class="category-tag">{cat}</span>' for cat in article['categories']])}
                        </div>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Lire l'actualité</a>
                    </div>"""

        # Ajout des bons plans
        if deals_articles:
            for article in deals_articles:
                html_content += f"""
                    <div class="article" data-category="{article['category']}">
                        <div class="article-image">
                            <a href="{article['lien']}" target="_blank">
                                <img src="{article['image_url']}" alt="{article['image_alt']}" loading="lazy">
                            </a>
                        </div>
                        <div class="article-meta">
                            <span class="date">{article['date']}</span>
                            <span class="author">Par {article['author']}</span>
                            <span class="comments">{article['comments']}</span>
                        </div>
                        <h2 class="titre">{article['titre']}</h2>
                        <div class="tags">
                            {' '.join([f'<span class="deal-tag">{tag}</span>' for tag in article['tags']])}
                        </div>
                        <p class="description">{article['description']}</p>
                        <a href="{article['lien']}" class="lien" target="_blank">Voir le bon plan</a>
                    </div>"""

        # Fermeture de la section IT-Connect et du document
        html_content += """
            </div>
        </div>"""

        # Ajout de la section YouTube après IT Connect
        html_content += """
        <div id="youtube" class="content">
            <h1 class="section-title">Chaînes YouTube Tech</h1>
            <div class="youtube-channels">
                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">IT-Connect</h2>
                        <p class="channel-description">Tutoriels et actualités informatiques - La chaîne officielle d'IT-Connect pour rester à jour sur les dernières technologies.</p>
                        <a href="https://www.youtube.com/@IT-Connect/videos" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>

                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">Hafnium</h2>
                        <p class="channel-description">Chaîne dédiée à la sécurité informatique, avec des tutoriels et des analyses approfondies sur la cybersécurité.</p>
                        <a href="https://www.youtube.com/@HafniumSecuriteInformatique" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>

                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">Monologix</h2>
                        <p class="channel-description">Actualités tech, analyses et décryptages sur les dernières tendances en informatique et nouvelles technologies.</p>
                        <a href="https://www.youtube.com/@Monologix" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>

                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">Cocadmin</h2>
                        <p class="channel-description">Tutoriels et astuces sur l'administration système, le réseau et la sécurité informatique.</p>
                        <a href="https://www.youtube.com/@cocadmin" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>

                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">La Techno</h2>
                        <p class="channel-description">Actualités technologiques et analyses des dernières innovations dans le monde de la tech.</p>
                        <a href="https://www.youtube.com/@LaTechno" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>

                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">zSecurity</h2>
                        <p class="channel-description">Formation et tutoriels en cybersécurité, hacking éthique et tests d'intrusion.</p>
                        <a href="https://www.youtube.com/@zSecurity" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>

                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">Paf le geek</h2>
                        <p class="channel-description">Actualités tech, tests de matériel et tutoriels informatiques accessibles à tous.</p>
                        <a href="https://www.youtube.com/@paflegeek" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>

                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">Underscore_</h2>
                        <p class="channel-description">Analyses approfondies sur la tech, la programmation et la culture numérique.</p>
                        <a href="https://www.youtube.com/@Underscore_" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>

                <div class="channel-card">
                    <div class="channel-content">
                        <h2 class="channel-title">Micode</h2>
                        <p class="channel-description">Vulgarisation de la programmation et de la sécurité informatique avec humour et pédagogie.</p>
                        <a href="https://www.youtube.com/@Micode" class="channel-link" target="_blank">
                            Voir la chaîne <span class="arrow">→</span>
                        </a>
                    </div>
                </div>
            </div>
        </div>"""

        # Ajout du CSS pour la section YouTube
        css_content = """
        /* Styles pour les articles ZATAZ */
        .article-content {
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            height: 100%;
            position: relative;
            background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        }

        .article-category {
            display: inline-block;
            padding: 0.4rem 0.8rem;
            background: #00b894;
            color: white;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .article .description {
            color: #636e72;
            line-height: 1.6;
            margin: 1rem 0;
            flex-grow: 1;
        }

        /* Styles pour la section YouTube */
        .youtube-channels {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .section-title {
            text-align: center;
            color: #2d3436;
            margin: 2rem 0;
            font-size: 2.5rem;
            font-weight: 600;
        }

        .channel-card {
            height: 100%;
            display: flex;
            flex-direction: column;
        }

        .channel-content {
            display: flex;
            flex-direction: column;
            height: 100%;
            justify-content: space-between;
        }

        .channel-description {
            flex-grow: 1;
        }

        .channel-link {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: #00b894;
            text-decoration: none;
            font-weight: 500;
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }

        .channel-link:hover {
            color: #00a884;
        }

        .channel-link .arrow {
            transition: transform 0.3s ease;
        }

        .channel-link:hover .arrow {
            transform: translateX(5px);
        }
        """

        # Insérer le CSS dans le head du document
        html_content = html_content.replace('</style>', f'{css_content}</style>')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"Le rapport a été généré dans le fichier: {output_file}")
        return output_file
            
    except Exception as e:
        print(f"Erreur lors du scraping: {str(e)}")
        return None

if __name__ == "__main__":
    # Configuration du parser d'arguments
    parser = argparse.ArgumentParser(description='Scraper pour les articles de ZATAZ')
    parser.add_argument('-t', '--title', 
                        help='Titre du fichier HTML généré (sans extension)',
                        default=None)
    
    # Parse les arguments
    args = parser.parse_args()
    
    # Lance le scraping avec le titre spécifié
    scrape_zataz(args.title)
