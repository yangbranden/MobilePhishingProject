# Goal of this script is to take the raw data from our tests and convert it into a CSV file with valuable output
# Input:
#   - text_logs.txt
#   - network_logs.txt
#   - page_sources.json
#
# Output (fields of CSV file):
#   - url (URL of website visited)
#   - start_time (timestamp indicating time when first request in visit began)
#   - phishing (whether the website is phishing or benign)
#   - All request headers (bitmap of all values in the network requests associated with a website visit)
#   - All response headers (bitmap of all values in the network responses associated with a website visit)


# TODO