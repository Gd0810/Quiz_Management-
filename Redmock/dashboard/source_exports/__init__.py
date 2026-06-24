from . import csv, json, text, word

EXPORTERS = {
    'text': text,
    'json': json,
    'word': word,
    'csv': csv,
}
