# Human Verification Spot-Check

**Generated**: 2025-12-01 21:26:52
**Source**: `evaluation/results/yelp_940_results.json`

## Instructions

For each company:
1. Visit the company website (domain column)
2. Look for About/Team/Contact page
3. Cross-reference with LinkedIn or Google search
4. Mark the verification status

---

## High Confidence Results (Expected: Correct)

These should mostly be correct. If many fail, pipeline has issues.

| # | Company | Domain | Contact | Title | Email | Conf | Sources | Verify |
|---|---------|--------|---------|-------|-------|------|---------|--------|
| 1 | EnviroBate | [envirobate.com](https://envirobate.com) | EnviroBate Inc. | Owner |  | 90 | google_maps_owner, s | [ ] |
| 2 | DRM United Demolition | [drmuniteddemolition.com](https://drmuniteddemolition.com) | D.R.M. United Demolition  | Owner |  | 90 | google_maps_owner | [ ] |
| 3 | Greenyard Landscaping & Demoli | [greenyard123.com](https://greenyard123.com) | Green Yard Landscaping | Owner |  | 90 | google_maps_owner, s | [ ] |
| 4 | Alliance Environmental Group | [alliance-enviro.com](https://alliance-enviro.com) | Alliance Environmental Se | Owner |  | 80 | google_maps_owner, s | [ ] |
| 5 | Property Hub | [property-hub-llc.com](https://property-hub-llc.com) | Property Hub | Owner |  | 90 | google_maps_owner, s | [ ] |
| 6 | Dylan’s Landscaping Company | [dlclawnnlandscape.com](https://dlclawnnlandscape.com) | Dylan’s landscaping compa | Owner |  | 90 | google_maps_owner | [ ] |
| 7 | X2C Motorwerkz | [x2cmotorwerkz.square.site](https://x2cmotorwerkz.square.site) | Librado Garza | Owner |  | 70 | serper_osint | [ ] |
| 8 | Souza's Land | [souzaslandco.com](https://souzaslandco.com) | Souza's Land Co | Owner |  | 90 | google_maps_owner | [ ] |
| 9 | Urgent Welding Eddie | [urgentweldingeddie.com](https://urgentweldingeddie.com) | Volz Welding | Owner |  | 90 | google_maps_owner | [ ] |
| 10 | The Handyman Boise | [thomas-andersen.square.site](https://thomas-andersen.square.site) | Handyman Leo LLC | Owner |  | 90 | google_maps_owner | [ ] |

## Low Confidence Results (Borderline)

These are uncertain. Check if pipeline correctly flagged them.

| # | Company | Domain | Contact | Title | Email | Conf | Sources | Verify |
|---|---------|--------|---------|-------|-------|------|---------|--------|
| 1 | Recovery Technology Solutions | [recoverytechnologysolutions.co…](https://recoverytechnologysolutions.co…) | Recovery Technology, LLC. | Owner |  | 30 | google_maps_owner, s | [ ] |
| 2 | Bings Complete Services, LLC | [bingsservices.square.site](https://bingsservices.square.site) | Bing's Construction CO. L | Owner |  | 30 | google_maps_owner | [ ] |
| 3 | Craig's Plumbing | [craigsplumbing.com](https://craigsplumbing.com) | CRI Plumbing | Owner |  | 30 | google_maps_owner, s | [ ] |
| 4 | Accelerated Engineering Servic | [accengserv.com](https://accengserv.com) | Accelerated Machine Desig | Owner |  | 30 | google_maps_owner, s | [ ] |
| 5 | 4 Seasons Property Maintenance | [4seasonsde.com](https://4seasonsde.com) | Four Season Property Serv | Owner |  | 30 | google_maps_owner, s | [ ] |
| 6 | DMV High Rise | [yessicafloreswork.wixsite.com](https://yessicafloreswork.wixsite.com) | Independence DMV | Owner |  | 30 | google_maps_owner | [ ] |
| 7 | Legit Workers | [legitworkers.com](https://legitworkers.com) | Akpan Emmanuel | Owner |  | 30 | serper_osint, social | [ ] |
| 8 | Spectrum Roofing & Renovations | [spectrumroofingfencesmetairie.…](https://spectrumroofingfencesmetairie.…) | Spectrum Construction Co. | Owner |  | 30 | google_maps_owner, s | [ ] |
| 9 | Cheap Hauling & Light Moving | [sanmateojunkremoval.com](https://sanmateojunkremoval.com) | Best Light Hauling and Mo | Owner |  | 30 | google_maps_owner | [ ] |
| 10 | NGP TECH | [ngptech.com](https://ngptech.com) | Dr.N.G.P. Institute of Te | Owner |  | 30 | google_maps_owner | [ ] |

## Failures (No Contact Found)

Verify if there IS a findable owner that pipeline missed.

| # | Company | Domain | Phone | Vertical | Verify |
|---|---------|--------|-------|----------|--------|
| 1 | Midwest Dredging & Pond Care | [iadredging.com](https://iadredging.com) |  | landscaping | [ ] |
| 2 | All Hours Plumbing, Heating &  | [allhoursplumbingslc.com](https://allhoursplumbingslc.com) |  | hvac | [ ] |
| 3 | Tex Auto Wrecking | [texautowrecking.com](https://texautowrecking.com) |  | auto_repair | [ ] |
| 4 | ABC Plumbing Heating and Air | [abcplumbingheatandair.com](https://abcplumbingheatandair.com) |  | hvac | [ ] |
| 5 | Norm's Moving & Hauling | [normsmoving.com](https://normsmoving.com) |  | movers | [ ] |
| 6 | Mr Drain | [mr-drain.ca](https://mr-drain.ca) |  | hvac | [ ] |
| 7 | Furniture Taxi Miami | [furnituretaximiami.com](https://furnituretaximiami.com) |  | movers | [ ] |
| 8 | Fiore & Sons | [fioreandsons.com](https://fioreandsons.com) |  | general_contrac | [ ] |
| 9 | Colton's Handyman Services | [coltonshandyman.wixsite.com](https://coltonshandyman.wixsite.com) |  | junk_removal | [ ] |
| 10 | Green Earth Automotive Recycli | [gearsrvpark.com](https://gearsrvpark.com) |  | auto_repair | [ ] |

---

## Verification Summary

| Category | Verified Correct | Verified Incorrect | Unable to Verify |
|----------|------------------|-------------------|------------------|
| High Confidence | /10 | /10 | /10 |
| Low Confidence | /10 | /10 | /10 |
| Failures (missed) | /10 | /10 | /10 |

### Notes

_Add observations here_
