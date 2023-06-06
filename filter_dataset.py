# This script filters the posts and finds posts that should be included in the (non-raw) dataset.

import time
import glob
import json
import sys
import os

# output filename
# don't use untrusted user input for this, it's passed directly to os.system - this is fine here though because it's just a static value

output_filename = "dataset/filtered/beepbox-archive.jsonl"

# profanity checker, wrapper for the rust binary

profanity_cache = {}

def check_profanity(text):
	if text in profanity_cache:
		return profanity_cache[text]

	# yes I know that I can use subprocess for this, but I'm not sure how. os.system + setting a os.environ value is a lot easier.

	os.environ["PROFANITY_CHECKER_INPUT"] = text
	status = os.system("./profanity-checker/target/release/profanity-checker ${PROFANITY_CHECKER_INPUT}")

	is_inappropriate = False

	if status == 1:
		is_inappropriate = True
	
	profanity_cache[text] = is_inappropriate
	return is_inappropriate

# main function, does most of the work

def main():
	if not os.path.isfile("dataset/raw/metadata.json"):
		print("Failed to find dataset/raw/metadata.json! Please download the dataset before running this script!")
		sys.exit(1)
	
	if not os.path.isfile("profanity-checker/target/release/profanity-checker"):
		print("Failed to find profanity-checker/target/release/profanity-checker! Please compile the profanity checker running this script!")
		sys.exit(1)
	
	start_time = time.time()

	# open the output file

	if not os.path.isdir("dataset/filtered"):
		os.mkdir("dataset/filtered")
	
	if os.path.isfile(output_filename):
		os.remove(output_filename)
	
	output = open(output_filename, "w")
	
	# parse dataset/raw/metadata.json

	f = open("dataset/raw/metadata.json", "r")
	metadata = json.load(f)
	f.close()

	# read the tweets

	files = glob.glob("dataset/raw/tweets/*.json")
	total = len(files)
	current = 0

	for filename in files:
		print("Reading:", filename, f"({current} / {total})")

		current += 1

		f = open(filename, "r")
		tweet = json.load(f)
		f.close()

		username = tweet["actualUserName"]
		content = tweet["message"]

		# We don't want official posts

		if username == "johnnesky" or username == "jummbus" or username == "beepboxco":
			continue

		# We don't want remixes

		if "remix" in content:
			continue
		
		# We don't want posts from accounts with inappropriate usernames

		if check_profanity(username):
			continue

		# yes, I understand that this approach is limited

		i = 0

		while len(tweet["songs"]) > i and isinstance(tweet["songs"][i], str):
			i += 1

		song = tweet["songs"][i]
		
		# I'm only going to include beepbox and jummbox for this, sorry

		songType = "beepbox"
		
		if song["fork"].startswith("jummbus.bitbucket.io"):
			songType = "jummbox"
		
		if not song["fork"].startswith("www.beepbox.co") and not song["fork"].startswith("jummbus.bitbucket.io"):
			continue
		
		# if all checks pass, save it to the dataset file

		songMetadata = {
			"author": username,
			"type": songType,
			"content": content,
			"url": "https://twitter.com/" + username + "/status/" + tweet["statusId"],
			"data": song["songData"]
		}

		output.write(json.dumps(songMetadata) + "\n")
	
	output.close()

	print("Compressing dataset with zstd...")

	os.system(f"zstd -f {output_filename} -o {output_filename}.zstd")

	#print("Deleting uncompressed dataset...")

	#os.remove(output_filename)

	timetaken = time.time() - start_time
	
	print(f"Finished in {timetaken}s!")

if __name__ == "__main__":
	main()