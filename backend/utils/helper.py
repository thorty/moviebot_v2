from backend.utils.tmdb.tmdb_api_client import get_movies_for_providers, get_basic_data_from_tmdb_for_titles, get_detail_data_from_tmdb_for_title, get_movies_with_recro
from backend.utils.tmdb.common import FreeProvider, Provider
# import module 

import traceback 


def choose_streaming_providers(userstreamingproviders: list[str], paymenttypes: list[str]) -> list[str]:
  """
  Filter streaming providers based on payment types.
  - If paymenttypes contains only 'free': filter against FreeProvider and return matched FreeProvider values
  - If paymenttypes contains 'rent' or other types: filter against Provider enum
  
  Uses improved fuzzy matching to handle variations like "MagentaTV" vs "Magenta TV+".
  Returns ALL matching canonical provider names from the respective enum.
  """
  # Determine which enum to use based on payment types
  if paymenttypes == ["free"]:
    # Only free content - use FreeProvider
    reference_providers = [fp.value for fp in FreeProvider]
  else:
    # Rent or mixed payment types - use full Provider enum
    reference_providers = [p.value for p in Provider]
  
  filtered_providers = []
  for user_provider in userstreamingproviders:
    user_lower = user_provider.lower()
    matched = False
    
    # Check for exact match first
    if user_provider in reference_providers:
      filtered_providers.append(user_provider)
      matched = True
    
    # If no exact match, do improved fuzzy matching
    if not matched:
      # Remove common separators for better matching (e.g., "MagentaTV" vs "Magenta TV+")
      user_normalized = user_lower.replace(' ', '').replace('+', '').replace('-', '')
      user_words = set(user_lower.split())
      
      for ref_provider in reference_providers:
        ref_lower = ref_provider.lower()
        ref_normalized = ref_lower.replace(' ', '').replace('+', '').replace('-', '')
        ref_words = set(ref_lower.split())
        
        # Multiple matching strategies:
        # 1. Normalized strings contain each other (handles "MagentaTV" vs "Magenta TV+")
        # 2. Word overlap (handles "Amazon Prime" vs "Amazon Prime Video")
        # 3. One string contains the other
        if (user_normalized in ref_normalized or ref_normalized in user_normalized or
            (user_words & ref_words) or 
            (user_lower in ref_lower) or (ref_lower in user_lower)):
          # Avoid duplicates
          if ref_provider not in filtered_providers:
            filtered_providers.append(ref_provider)
  
  return filtered_providers
  
  
  
def get_movie_data(input: dict):
  try:
    titles = input["titles"]
    print(f"_get_movie_data titles input: ", titles)
    inputlist = titles.split(",")
    inputlist = [x.strip(' ') for x in inputlist]      
    result = get_basic_data_from_tmdb_for_titles(inputlist)
    print(f"get_movie_data result: ", result)
    return result
  except:    
     traceback.print_exc() 
     return None

def get_filtered_titles_tmdb(titles: list, userstreamingproviders: list[str]) -> dict:
  """Get filtered titles. Accepts list of strings or list of dicts with media_type."""
  try:
    inputlist = titles
    providers = userstreamingproviders
    print(f"_get_movie_data titles input: ", titles, "filtered by providers: ", providers)
    result = get_movies_for_providers(inputlist, providers)    
    print(f"get_tmdb_filtered_movies result: ",result)
    return result  
  except:
      traceback.print_exc() 
      return None 
    
def get_filtered_recros_titles_tmdb(titles: list[str], userstreamingproviders: list[str]) -> dict:
  try:
    inputlist = titles
    providers = userstreamingproviders
    print(f"_get_movie_data titles input: ", titles, "filtered by providers: ", providers)
    #inputlist = titles.split(",")
    #inputlist = [x.strip(' ') for x in inputlist]
    result = get_filtered_recros_titles_tmdb(inputlist, providers)
    print(f"get_recro_movies result: ",result)
    return result  
  except:
      traceback.print_exc() 
      return None     

def get_streaming_providers_tmdb(titles: list[str]):
  try:
    print(f"get_streaming_providers","titles=",titles)
    result = get_basic_data_from_tmdb_for_titles(titles)
    print(f"get_streaming_providers","result:", result)
    return result
  except:
     traceback.print_exc() 
     return None

def get_detail_moviedata(title: str):
  try:
    print(f"get_movie_data_from_tmdb","title=",title)
    fulldata = get_detail_data_from_tmdb_for_title(title)
    print(f"get_detail_moviedata","result:", fulldata)
    return fulldata
  except:
     traceback.print_exc() 
     return None
  

