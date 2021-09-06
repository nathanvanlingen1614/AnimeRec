import requests
import json
import secrets
from MALToken import MALToken
import pandas as pd
import re
import MALScraper
import bs4
import os

class MALBuddy:
    def __init__(self, client_info_fp,token_filepath=None):
        self.token = MALToken(client_info_fp, token_filepath)

    def get_anime_list(self, user: str, limit=500) -> pd.DataFrame:
        """Returns a DataFrame of the given users Animelist

        Keyword Arguments:
            limit -- max number of entries to load from the user's animelist
        """
        url = f"https://api.myanimelist.net/v2/users/{user}/animelist?fields=list_status&limit={limit}"

        resp = requests.get(url, headers={"Authorization": f"Bearer {self.token.get_access_token()}"})

        if (resp.ok):
            mal = resp.json()['data']
        else:
            token.refresh_token()
            resp = requests.get(url, headers={"Authorization": f"Bearer {self.token.get_access_token()}"})
            if (not resp.ok):
                print("Error requesting anime list. Aborting...")
                return

        data = []
        for anime in mal:
            dictionary = anime['node']
            dictionary.update(anime['list_status'])
            data.append(dictionary)

        mal_df = pd.DataFrame(data)
        return mal_df

    def get_token(self) -> MALToken:
        return self.token.get_token()

    def generate_ratings(self, anime: str, num_pages=99) -> pd.DataFrame:
        """Webscrapes latest 99 pages of ratings from MAL for the given anime"""
        if num_pages > 99:
            print("Cannot scrape more than 99 pages!")
            return
        
        pages = MALScraper.download_all_ratings(anime, num_pages)
        user_list = []
        rating_list = []
        for page in pages:
            if page == None:
                break
            soup = bs4.BeautifulSoup(page, features='lxml')
            user_list += MALScraper.parse_users(soup)
            rating_list += MALScraper.parse_ratings(soup)

        user_ratings = pd.DataFrame({"user": user_list, 'rating': rating_list})
        user_ratings = user_ratings.drop_duplicates(subset=['user'], keep='first')  # drop duplicates, keep most recent
        user_ratings = user_ratings[user_ratings['rating'] != '-']
        user_ratings = user_ratings.astype({'rating': 'int32'})
        user_ratings = user_ratings.reset_index(drop=True)

        return user_ratings


    def generate_and_write_ratings(self, anime: str, fp=None, folder='anime_ratings', num_pages=99) -> pd.DataFrame:
        """Webscrapes latest 99 pages of rating from MAL and then writes the data to a
        json file"""
        if os.path.exists(folder):
            save_folder = f'/{folder}'
        else:
            print(f"Error, folder {folder} not found!")
            return
        

        ratings = self.generate_ratings(anime,num_pages=num_pages)
        if fp is None:
            fp = os.path.join(folder, f'{anime}.json')
        with open(fp, 'w') as file:
            json.dump(ratings.to_dict(), file)
        file.close()
        print(f"\nRatings saved to {fp} ")
        return ratings

    def load_ratings(self, anime: str, folder='anime_ratings') -> pd.DataFrame:
        if os.path.exists(folder):
            save_folder = folder
        else:
            print(f"Error, folder {folder} not found!")
            return

        fp = os.path.join(save_folder, f'{anime}.json')
        print(fp)
        
        with open(fp, 'r') as file:
            ratings = json.load(file)
        file.close()
        return pd.DataFrame(ratings)




