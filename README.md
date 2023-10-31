# Delivery_patterns

## Description


## Dependencies
import pandas as pd
import json
import re
import roman


## 1. Preprocessing:
	input: raw-data

	i. Split street name and house no in different columns. "split_street_and_number()"
	ii. Remove "AM" and "IM" Prefixes. "remove_prefix()"
	iii. Replace Roman numerals with integers (II LEEGMOORWEG with 2 LEEGMOORWEG  ). "replace_roman_numerals()"
	iv. Replace dash with space in Straße_Empfänger. "replace_dash_with_space()"
	v. Split the Stadt_Empfänger column on '/'. "split_on_slash()"
	vi. Split the Haus_Empfänger column on '-' or '+', and keep the first part before the '-' or '+'. "split_on_dash_or_plus()"
	vii. Clean and convert the "Gewicht" column to numeric
	viii. Calculate the mean of the "Gewicht" column
	ix. Fill NA values in "Gewicht" column with the mean
	x. Clean and convert the "Frachtkosten" column to numeric
	xi. Calculate the mean of the "Frachtkosten" column
	xii. Fill NA values in "Frachtkosten" column with the mean
	xiii. Convert "Beladedatum" column to datetime format
	xiv. Extract week number using strftime and write to new column "Kalenderwoche"

	Output: pre-processed-data.csv





## Visuals


## Installation


## Usage


## Support


## Roadmap


## Contributing


## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
