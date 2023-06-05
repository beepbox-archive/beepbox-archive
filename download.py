import requests_cache
import requests
import json
import os

requests_cache.install_cache("beepbox-archive-cache")

# scrapes the content of https://twitter-archive.beepbox.co/ to grab the JSON data

def scrape_webpage():
	# fetch the webpage with requests.get()
	
	response = requests.get("https://twitter-archive.beepbox.co/")
	
	if response.status_code != 200:
		raise Exception(f"Expected status code 200, got {response.status_code}. It's likely that we've been ratelimited!")
	
	contents = response.text
	
	# set up the dict we're going to write to later
	
	raw_dataset = {
		"allDates": [],
		"allUsers": [],
		"shortTweets": []
	}
	
	# detect and scrape the JSON data from the JavaScript code
	# this may sound really stupid (and it is), but I think you'd be surprised by how well this actually works - somehow this worked on the first try with no issues.
	
	lines = contents.split("\n")
	i = 0
	
	while len(lines) > i:
		line = lines[i]
		
		if line == "const allDates =":
			raw_dataset["allDates"] = json.loads(lines[i + 1])
			i += 2
			continue
		
		if line == "const allUsers =":
			raw_dataset["allUsers"] = json.loads(lines[i + 1])
			i += 2
			continue
		
		if line == "const shortTweets =":
			raw_dataset["shortTweets"] = json.loads(lines[i + 1])
			i += 2
			continue
		
		if len(raw_dataset["allDates"]) > 0 and len(raw_dataset["allUsers"]) > 0 and len(raw_dataset["shortTweets"]) > 0:
			break
		
		i += 1

	return raw_dataset

# fetch the JSON data for a specific tweet, basically just a fancy requests.get() wrapper

def fetch_tweet(tweet_id):
	response = requests.get(f"https://twitter-archive.beepbox.co/tweets/{tweet_id}.json")
	
	if response.status_code != 200:
		raise Exception(f"Expected status code 200, got {response.status_code}. It's likely that we've been ratelimited!")
	
	return response.json()

# main function, basically just a wrapper for everything else

def main():
	if not os.path.isdir("dataset"):
		os.mkdir("dataset")
	
	if not os.path.isdir("dataset/raw"):
		os.mkdir("dataset/raw")
	
	if not os.path.isdir("dataset/raw/tweets"):
		os.mkdir("dataset/raw/tweets")
	
	print("Scraping the webpage...")
	
	raw_dataset = scrape_webpage()
	
	f = open("dataset/raw/metadata.json", "w")
	f.seek(0)
	f.write(json.dumps(raw_dataset, indent="\t"))
	f.close()
	
	print("Downloading data...")
	
	for i, tweet in enumerate(raw_dataset["shortTweets"]):
		if os.path.isfile(f"dataset/raw/tweets/{i}.json"):
			continue
		
		tweet_data = fetch_tweet(i)
		
		f = open(f"dataset/raw/tweets/{i}.json", "w")
		f.seek(0)
		f.write(json.dumps(tweet_data, indent="\t"))
		f.close()

if __name__ == "__main__":
	main()
