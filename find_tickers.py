import reticker
import sys

ticker_match_config = reticker.TickerMatchConfig(prefixed_uppercase=True, unprefixed_uppercase=True)
extractor = reticker.TickerExtractor(deduplicate=True, match_config=ticker_match_config)

def find_stonks(msg):
    return extractor.extract(msg)

if __name__ == "__main__":
    result = find_stonks(sys.argv[1])
    print(result)
