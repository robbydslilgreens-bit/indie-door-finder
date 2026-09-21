# indie-door-finder

A small, free tool that lists independent cafes, juice bars, health-food stores, delis and grocers near any place, so a food or drink maker can build a first list of local retail doors to visit or pitch.

It uses only OpenStreetMap services (Nominatim to geocode, Overpass to search). No API keys, no accounts, and no third-party Python packages.

```
python door_finder.py --city "Asheville, NC" --radius-mi 10 --out doors.csv
python door_finder.py --lat 35.5951 --lon -82.5515 --radius-mi 15 --out doors.csv
python door_finder.py --city "Front Royal, VA" --radius-mi 25 --broad   # also corner stores and supermarkets
```

You get a CSV with name, category, address, phone, website, email (when OpenStreetMap has one), distance in miles, and a link back to the OpenStreetMap entry. A sample run for Asheville, NC (8 miles) is in [`sample-asheville.csv`](sample-asheville.csv): 45 independent candidates, 14 with a website, 2 with an email listed.

## What it filters

- Anything tagged with a brand or operator (that is how OpenStreetMap marks chains).
- Shops whose name matches a list of common national and regional chains (`CHAINS` in the script; add your own).
- Duplicates at the same spot.

## Limits you should know about

- **OpenStreetMap coverage is uneven.** Small rural shops are often missing, and tags are volunteer-entered. In the sample above, only 2 of 45 shops listed an email. Use the output as a candidate list, not a verified one.
- **It finds shops; it does not find buyers.** Look at each shop's website or call before you pitch, and verify any email address before you send to it.
- **Fair use.** One geocode request and one Overpass request per run. Please don't loop it over hundreds of towns; the public servers are free because people are polite with them.
- Independent is a guess. A shop can be a franchise or small chain without a brand tag. Skim the list.

## Where this comes from

We make a small-batch beverage (Robby Ds Lil Greens, in Virginia's Shenandoah Valley) and sell it through independent stores. This is a stripped-down, standalone version of the OpenStreetMap step in our own prospecting, published in case it saves another maker an afternoon.

If you want the rest of the method (how to find the buyer, what to say, how to follow up after a sample), we wrote it up:

- Free: the [weekly door tracker](https://robbydslilgreens.com/indie-retail-doors?utm_source=github&utm_medium=readme&utm_campaign=door-finder) and the [guides on our blog](https://robbydslilgreens.com/answers/tools-for-getting-into-indie-retail-stores?utm_source=github&utm_medium=readme&utm_campaign=door-finder).
- $19: [The Indie Retail Playbook](https://shop.robbydslilgreens.com/products/the-indie-retail-playbook-get-your-food-or-drink-into-independent-stores?utm_source=github&utm_medium=readme&utm_campaign=door-finder).

The tool is MIT licensed and works fine without any of that.

## License

MIT. Map data is from OpenStreetMap contributors, available under the [ODbL](https://www.openstreetmap.org/copyright); if you publish a list built from it, credit them.
