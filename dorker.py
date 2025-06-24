import logging
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from rich.console import Console
from rich.progress import track
from pyfiglet import Figlet

console = Console()
logging.basicConfig(
    filename="dorking.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def print_banner():
    banner = Figlet(font='slant').renderText('Diddy Dorker v1')
    console.print(f"[bold green]{banner}[/bold green]")

def setup_session(proxy=None):
    session = requests.Session()
    ua = UserAgent()
    session.headers.update({"User-Agent": ua.random})
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
        logging.info(f"Using proxy: {proxy}")
    return session

def read_dorks(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        console.print(f"[red][ERROR] Dorks file {file_path} not found[/red]")
        raise

def url_encode(query):
    return quote(query, safe="")

def search_duckduckgo(query, session):
    url = "https://html.duckduckgo.com/html/"
    data = {"q": url_encode(query)}
    try:
        response = session.post(url, data=data, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = [
            link.get("href") for link in soup.select(".result__url")
            if link.get("href") and not any(x in link.get("href") for x in ["duckduckgo.com", "about:"])
        ]
        return links
    except Exception as e:
        logging.warning(f"DuckDuckGo failed for {query}: {e}")
        return []

def check_url_live(url):
    try:
        r = requests.get(url, timeout=5)
        return url if r.status_code in [200, 301, 302, 403, 401] else None
    except:
        return None

def filter_live_urls(urls):
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_url_live, urls))
    return [url for url in results if url]

def main():
    print_banner()

    console.print("[yellow][+] site :( :[/yellow]", end=" ")
    target = input().strip()

    console.print("[green][+] dork file :[/green]", end=" ")
    dorks_file = input().strip()

    console.print("[yellow][+] results all or number :[/yellow]", end=" ")
    user_choice = input().strip().lower()
    if user_choice == "all":
        total_results = float("inf")
    else:
        try:
            total_results = int(user_choice)
            if total_results <= 0:
                raise ValueError
        except ValueError:
            console.print("[red][ERROR] enter a positive integer or 'all'[/red]")
            return

    console.print("[green][+] save output? (Y/N):[/green]", end=" ")
    save_output = input().strip().lower()
    output_file = "results.txt"
    if save_output == "y":
        console.print("[yellow][+] output filename :[/yellow]", end=" ")
        output_file_input = input().strip()
        if output_file_input:
            output_file = output_file_input if output_file_input.endswith(".txt") else f"{output_file_input}.txt"

    proxy = None
    console.print("[green][+] enter proxy URL or leave empty for none:[/green]", end=" ")
    proxy_input = input().strip()
    if proxy_input:
        proxy = proxy_input

    session = setup_session(proxy)

    try:
        dorks = read_dorks(dorks_file)
        console.print(f"[blue][INFO] Loaded {len(dorks)} dorks[/blue]")
    except Exception:
        return

    console.print("\n[green][INFO] Searching... Please wait...diddy is touching the internet...[/green]\n")

    all_results = []
    fetched = 0

    for dork in track(dorks, description="lemme touch the internet rq..."):
        if fetched >= total_results:
            break

        query = f"site:{target} {dork}" if target else dork
        logging.info(f"Query: {query}")
        console.print(f"[cyan][+] Searching: {query}[/cyan]")

        links = search_duckduckgo(query, session)

        if links:
            live_links = filter_live_urls(links)
            all_results.extend(live_links)
            fetched += len(live_links)
            for link in live_links:
                console.print(f"[green][+] {link}[/green]")
        else:
            console.print(f"[red][-] No results for {query}[/red]")

        time.sleep(random.uniform(1, 3))

    if save_output == "y" and all_results:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(all_results))
            console.print(f"\n[bold green]✓ Saved {len(all_results)} live URLs to {output_file}[/bold green]")
        except Exception as e:
            console.print(f"[red][ERROR] Failed to save results: {e}[/red]")

    console.print("\n[bold green]✓ diddy did it[/bold green]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red][!] diddy stopped[/red]")
