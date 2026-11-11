# Hero image prompts: What Medicare can learn from the VA’s $11 drug copay

Target: 1680x1080 landscape. Generate wide (3:2 or 16:9), at least 1680 pixels wide so `hero fit` does not
have to upscale; the crop is done with `~/.claude/d4tp-process/hero fit`.

Eric's idea: a veteran at a pharmacy counter paying the copay in cash, so the reader can see it is $11. The
VA's copay for a 30-day supply of a brand-name drug is $11 in 2026 (VA copay rates, DATASETS.md). The image
is symbolic: the VA bills copays afterward, and many VA prescriptions come by mail. So the prompts show a
plain pharmacy with no VA seal or signage, and the $11 is shown twice (a $10 bill and a $1 bill, and a
register display), in case the generator garbles the numbers.

## Prompt 1 (photo, older veteran)

Photorealistic, wide landscape, warm and calm. An older American veteran in his seventies stands at a
pharmacy counter, seen from the side and slightly behind his shoulder. He wears a dark navy veteran's ball cap
with a plain embroidered service ribbon and no words, and a tan jacket. With one hand he lays a ten-dollar
bill and a one-dollar bill flat on the counter, in sharp focus. Next to the bills, a small white paper
pharmacy bag sits on the counter. A friendly pharmacist in a white coat stands behind the counter, softly out
of focus. A small customer-facing register display on the counter reads "$11.00" in clear green digits.
Shelves of medicine fill the background, blurred. Soft, natural light, shallow depth of field, 50mm lens.
The veteran and the bills fill the left two-thirds of the frame; the register and pharmacist are on the right.

Avoid: any text other than "$11.00", VA seals or logos, flags, store names, real drug or store brands,
signs with words.

## Prompt 2 (variant: close on the counter)

Photorealistic, wide landscape. Close view of a pharmacy counter at eye level. The weathered hands of an
older veteran place a ten-dollar bill and a one-dollar bill on the counter. The sleeve of an olive green
military-style field jacket shows at the wrist. A white paper pharmacy bag with a stapled prescription
receipt sits beside the bills. A customer-facing register display reads "$11.00". Behind the counter, a
pharmacist in a white coat is out of focus, with blurred shelves of medicine. Warm, soft light, shallow
depth of field.

Avoid: any text other than "$11.00", VA seals or logos, flags, faces in sharp focus, store names, real drug
or store brands, signs with words.

## Prompt 3 (variant: woman veteran)

Same as Prompt 1, but the veteran is a woman in her sixties with short gray hair, wearing a dark veteran's
ball cap with a plain embroidered service ribbon and no words, and a denim jacket.

## Chosen

File: images/va-vs-medicare-drug-prices-hero-source.<ext>
Alt (under 500 characters): written once the image is chosen.
