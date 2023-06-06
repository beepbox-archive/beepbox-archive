// this is just a wrapper for rustrict (because rustrict is the best profanity filter library ever)

use rustrict::CensorStr;

fn main() {
	if let Some(text) = std::env::args().nth(1) {
		if text.is_inappropriate() {
			std::process::exit(1);
		}
	}
}
