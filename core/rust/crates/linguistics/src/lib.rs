//! Basic transliteration utilities (stubs).
use regex::Regex;

pub fn latin_to_arabic_stub(input: &str) -> String {
    // simple placeholder: reverse string & add marker
    input.chars().rev().collect::<String>() + "·ar"
}

pub fn sga_encode_stub(input: &str) -> String {
    let re = Regex::new(r"[aeiou]").unwrap();
    re.replace_all(input, "∴").to_string()
}
