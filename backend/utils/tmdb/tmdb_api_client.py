#tmdb api
# moviedb tool singe title search
import requests
import json
from difflib import get_close_matches
import os
import dotenv

# If you're curious of all the loggers
#print(streamlit.logger._loggers)  

#streamlit_root_logger = logging.getLogger(streamlit.__name__)

dotenv.load_dotenv()

headers = {
    "accept": "application/json",
    "Authorization": os.environ["tmdb_bearer"]    
}


# Helper function to normalize TV show vs movie fields
def normalize_media_item(item, media_type="movie"):
    """Normalize TV show and movie data to consistent format"""
    if not item:
        return None
    
    # TV shows use 'name' instead of 'title'
    if 'name' in item and 'title' not in item:
        item['title'] = item['name']
    
    # TV shows use 'first_air_date' instead of 'release_date'
    if 'first_air_date' in item and 'release_date' not in item:
        item['release_date'] = item['first_air_date']
    
    return item



def get_movies_with_recro(titles: list, providers: list[str]):
  """Get movies/TV shows with recommendations. Accepts list of strings or list of dicts with media_type."""
  print("get_movies_with_recro", titles)
  movies =[]
  # get movies from tmdb from given titles
  for item in titles:
    # Support both old format (string) and new format (dict with media_type)
    if isinstance(item, dict):
      title = item.get('title')
      media_type = item.get('media_type', 'movie')
    else:
      title = item
      media_type = 'movie'
    
    if not title:
      continue
      
    movie = get_basic_data_from_tmdb_for_title(title, media_type)
    if movie:
      movies.append(movie)
  # add similar recommendations from tmdb
  if movies:
    # Use media_type from first movie
    first_media_type = movies[0].get('media_type', 'movie')
    similar_movies = get_recro_movies(movies, first_media_type)
    if similar_movies:
      movies = movies + similar_movies
  # filter for providers
  rsult_movies = filter_movies(movies, providers)
  if rsult_movies and len(rsult_movies) > 5:
    rsult_movies = rsult_movies[:4]    
  fulldata_as_string = create_data_list(rsult_movies)
  return fulldata_as_string
  
def get_movies_for_providers(titles: list, providers: list[str]):
  """Get movies/TV shows for providers. Accepts list of strings or list of dicts with media_type."""
  print(f"get_basic_data_from_tmdb_for_titles",titles)
  movies =[]
  # get movies from tmdb from given titles
  for item in titles:
    # Support both old format (string) and new format (dict with media_type)
    if isinstance(item, dict):
      title = item.get('title')
      media_type = item.get('media_type', 'movie')
    else:
      title = item
      media_type = 'movie'
    
    movie = get_basic_data_from_tmdb_for_title(title, media_type)
    if movie:
      movies.append(movie)  
  # filter for providers
  rsult_movies = filter_movies(movies, providers)
  return rsult_movies

def get_basic_data_from_tmdb_for_titles(titles: list):
  """Get basic data for titles. Accepts list of strings or list of dicts with media_type."""
  print("get_basic_data_from_tmdb_for_titles", titles)
  movies =[]
  for item in titles:
    # Support both old format (string) and new format (dict with media_type)
    if isinstance(item, dict):
      title = item.get('title')
      media_type = item.get('media_type', 'movie')
    else:
      title = item
      media_type = 'movie'
    
    if not title:
      continue
      
    movie = get_basic_data_from_tmdb_for_title(title, media_type)
    if movie:
      movies.append(movie)
  fulldata_as_string = create_data_list(movies)
  return fulldata_as_string


def get_detail_data_from_tmdb_for_titles(titles: list):
  """Get detailed data for titles. Accepts list of strings or list of dicts with media_type."""
  print("get_detail_data_from_tmdb_for_titles", titles)
  movies =[]
  for item in titles:
    # Support both old format (string) and new format (dict with media_type)
    if isinstance(item, dict):
      title = item.get('title')
      media_type = item.get('media_type', 'movie')
    else:
      title = item
      media_type = 'movie'
    
    if not title:
      continue
      
    movie = get_detail_data_from_tmdb_for_title(title, media_type)
    if movie:
      movies.append(movie)
  return movies

def get_basic_data_from_tmdb_for_title(title: str, media_type: str = "movie"):
  """Get basic data for a title. Falls back to other media_type if not found."""
  try:
    print(f"get_movie_data_from_tmdb","title=",title,"media_type=",media_type)
    fulldata = create_basic_movie_data(title, media_type)
    
    # Fallback: If not found, try the other media type
    if not fulldata:
      fallback_type = "tv" if media_type == "movie" else "movie"
      print(f"[FALLBACK] Title '{title}' not found as {media_type}, trying {fallback_type}")
      fulldata = create_basic_movie_data(title, fallback_type)
    
    return fulldata
  except Exception as e:
     print(f"[ERROR] get_basic_data_from_tmdb_for_title: {e}")
     return None

def get_detail_data_from_tmdb_for_title(title: str, media_type: str = "movie"):
  """Get detailed data for a title. Falls back to other media_type if not found."""
  try:
    print(f"get_movie_data_from_tmdb","title=",title,"media_type=",media_type)
    fulldata = create_movie_data(title, media_type)
    
    # Fallback: If not found, try the other media type
    if not fulldata:
      fallback_type = "tv" if media_type == "movie" else "movie"
      print(f"[FALLBACK] Title '{title}' not found as {media_type}, trying {fallback_type}")
      fulldata = create_movie_data(title, fallback_type)
    
    return fulldata
  except Exception as e:
     print(f"[ERROR] get_detail_data_from_tmdb_for_title: {e}")
     return None

def get_recro_movies(movies, media_type="movie"):  
  if len(movies) > 0:
    searchId = movies[0]["id"]
    results = find_smilar_movies(searchId, media_type)
    if results:
      movies = parse_movies_from_search(results, media_type)
    return movies

def find_smilar_movies(id, media_type="movie"):
  endpoint = "movie" if media_type == "movie" else "tv"
  url = f"https://api.themoviedb.org/3/{endpoint}/{id}/recommendations?language=en-US&page=1"
  response = requests.get(url, headers=headers)  
  if response.status_code == 200:
    data = json.loads(response.text)  
    return data
  return None  

def parse_movies_from_search(results, media_type="movie"):
  movies=[]
  for movie in results["results"]:
    if movie and "id" in movie:
      # Normalize TV show fields to movie format
      movie = normalize_media_item(movie, media_type)
      
      id = get_movie_id(movie)
      providers = get_watch_providers(id, media_type)
      flatproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"),"flatrate" )
      rentproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"),"rent" )

      filtered_data = {'title': movie['title'], 'flatproviders': flatproviders, 'rentproviders': rentproviders, 'overview': movie.get('overview', ''),
                      'release_date': movie.get('release_date', ''), 'id': id,
                      }
      movies.append(filtered_data)
  return movies

def find_movie_basic(title, lang, media_type="movie"):
  original_title = title  # Keep original for matching
  title_encoded = title.replace(' ', '+')
  endpoint = "movie" if media_type == "movie" else "tv"
  url = f"https://api.themoviedb.org/3/search/{endpoint}?include_adult=false&language={lang}&page=1&query={title_encoded}"

  response = requests.get(url, headers=headers)

  if response.status_code == 200:
    data = json.loads(response.text)

    if "results" in str(data) and len(data["results"]) > 0:
      movie = get_movie_form_search(data["results"], original_title, media_type)
      if movie:
        # Normalize TV show fields to movie format
        movie = normalize_media_item(movie, media_type)
      return movie

  return None

def find_movie(title, lang, media_type="movie"):
  original_title = title  # Keep original for matching
  title_encoded = title.replace(' ', '+')
  endpoint = "movie" if media_type == "movie" else "tv"
  url = f"https://api.themoviedb.org/3/search/{endpoint}?include_adult=false&language={lang}&page=1&query={title_encoded}"

  response = requests.get(url, headers=headers)

  if response.status_code == 200:
    data = json.loads(response.text)
    print("find_movie for", title, "response: ",data)

    if "results" in str(data) and len(data["results"]) > 0:
      print("movie found!")
      movie = get_movie_form_search(data["results"], original_title, media_type)
      if movie:
        movie = get_detail_moviedata(get_movie_id(movie), media_type)
        movie = json.loads(movie)
        # Normalize TV show fields
        movie = normalize_media_item(movie, media_type)
      return movie

  return None


def get_movie_id(movie):
  #print(f"get_movie_id for ", movie)
  if movie:
      return movie["id"]


def get_watch_providers(id, media_type="movie"):
  endpoint = "movie" if media_type == "movie" else "tv"
  url = f"https://api.themoviedb.org/3/{endpoint}/{id}/watch/providers"
  response = requests.get(url, headers=headers)
  return response.text

def get_detail_moviedata(id, media_type="movie"):
  endpoint = "movie" if media_type == "movie" else "tv"
  url = f"https://api.themoviedb.org/3/{endpoint}/{id}?language=en-US"
  response = requests.get(url, headers=headers)
  return response.text


def filter_watch_providers(data, lang):
  # Filter data under "<lang>"
  data = json.loads(data)
  if lang in data["results"]:
    filtered_data = data["results"][lang]
    # Print the filtered JSON
    return filtered_data



def get_watch_providers_via_subtype(data, subtype):
#subtype = "bye", "rent", "flatrate"

  provider_names=[]
  if subtype in str(data):
    filtered_data = data[subtype]
    if len(filtered_data) > 0:
      provider_names = [item['provider_name'] for item in filtered_data]

  return provider_names


def create_movie_data(title, media_type="movie"):
  movie = find_movie(title, "de-DE", media_type)
  if movie and "id" in movie:
    id = get_movie_id(movie)
    providers = get_watch_providers(id, media_type)
    flatproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"),"flatrate" )
    rentproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"),"rent" )
    buyproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"),"buy" )
    genres = [x['name'] for x in movie.get('genres', [])]
    prodcountries = [x['name'] for x in movie.get('production_countries', [])]
    
    filtered_data = {'title': movie['title'], 'flatproviders': flatproviders, 'rentproviders': rentproviders, 'buyproviders': buyproviders,
                     'adult': movie.get('adult', False), 'genres': genres, 'budget': movie.get('budget', 0), 'overview': movie.get('overview', ''),
                     'popularity': movie.get('popularity', 0), 'poster_path': movie.get('poster_path', ''), 'release_date': movie.get('release_date', ''),
                     'runtime': movie.get('runtime', 0), 'revenue': movie.get('revenue', 0), 'vote_average': movie.get('vote_average', 0), 'vote_count': movie.get('vote_count', 0),
                     'production_countries': prodcountries, 'media_type': media_type
                     }
    return filtered_data

def create_basic_movie_data(title, media_type="movie"):
  movie = find_movie_basic(title, "de-DE", media_type)
  if movie and "id" in movie:
    id = get_movie_id(movie)
    providers = get_watch_providers(id, media_type)
    flatproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"),"flatrate" )
    rentproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"),"rent" )
    buyproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"),"buy" )

    filtered_data = {'title': movie['title'], 'flatproviders': flatproviders, 'rentproviders': rentproviders, 'overview': movie.get('overview', ''),
                     'release_date': movie.get('release_date', ''), 'id': id, 'media_type': media_type
                     }
    return filtered_data




def create_recommendation_data(item):

  ## just importent info
  filtered_data = {'title': item['title'], 'flatproviders': item['flatproviders'], 'rentproviders': item['rentproviders'], 'buyproviders': item['buyproviders']}
  ##filter only movies that are for streaming or rent available
  item =filtered_data

  if 'flatproviders' in item and len(item['flatproviders']) > 0:
      if 'rentproviders' in item and len(item['rentproviders']) > 0:
           return {"title":item['title'], 'flatproviders': item['flatproviders'], 'rentproviders': item['rentproviders']}
      else:
          return {"title":item['title'],'flatproviders': item['flatproviders']}
  elif 'rentproviders' in item and len(item['rentproviders']) > 0:
     return {"title":item['title'],'rentproviders': item['rentproviders']}

def get_movie_form_search(data: dict, search: str, media_type="movie"):
  try:
      # TV shows use 'name' instead of 'title'
      # Also check 'original_name' and 'original_title' for better matching
      if media_type == "tv":
        titles = [x.get("name", x.get("title", "")) for x in data]
        original_titles = [x.get("original_name", x.get("original_title", "")) for x in data]
      else:
        titles = [x.get("title", x.get("name", "")) for x in data]
        original_titles = [x.get("original_title", x.get("original_name", "")) for x in data]
      
      # Try matching with localized title first
      title_match = closeMatches(titles, search)
      if title_match:
        title = title_match[0]
        if media_type == "tv":
          movie = [x for x in data if x.get('name', x.get('title', '')) == title]
        else:
          movie = [x for x in data if x.get('title', x.get('name', '')) == title]
        return movie[0] if movie else None
      
      # Fallback: Try matching with original title (often English)
      original_match = closeMatches(original_titles, search)
      if original_match:
        original_title = original_match[0]
        if media_type == "tv":
          movie = [x for x in data if x.get('original_name', x.get('original_title', '')) == original_title]
        else:
          movie = [x for x in data if x.get('original_title', x.get('original_name', '')) == original_title]
        return movie[0] if movie else None
      
      return None
  except Exception as e:
    print(f"[ERROR] get_movie_form_search: {e}")
    return None

# Function to find all close matches of
# input string in given list of possible strings
def closeMatches(patterns, word):
     return get_close_matches(word, patterns)

def create_data_list(fulldata):
  movieinfoasstring=""
  for movie_info in fulldata:
     formatted_info = f"Title: {movie_info['title']}, "
     formatted_info += f"Overview: {movie_info['overview']}, "
     formatted_info += f"flatproviders: {', '.join(movie_info['flatproviders'])}, "
     formatted_info += f"rentproviders: {', '.join(movie_info['rentproviders'])}\n"
     movieinfoasstring+=formatted_info
  return movieinfoasstring

def filter_movies(movies: list, providers: list[str]):  
  filtered_list = movies
  if providers and len(providers) > 0:  
    filtered_list = filterforproviders(movies, providers)
  return filtered_list

def filterforproviders(movies, providers):
  filtered_list = [
    d for d in movies
    if (
        'flatproviders' in d and any(
            any(provider.lower() in fp.lower() for fp in d['flatproviders'])
            for provider in providers
        )
    ) or (
        'rentproviders' in d and any(
            any(provider.lower() in rp.lower() for rp in d['rentproviders'])
            for provider in providers
        )
    )
  ]
  return filtered_list
