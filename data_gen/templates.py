"""Text templates for synthetic feedback. `{product}` is replaced by the product name."""

# Rating comments, keyed by (category, sentiment).
RATING_COMMENTS = {
    ("fit_sizing", "negative"): [
        "The {product} runs really small, I had to size up.",
        "Ordered my usual size M but the {product} is way too tight.",
        "Sleeves on the {product} are too short and the shoulders pinch.",
        "Size chart is wrong for the {product}, it does not fit at all.",
        "The {product} looks nice but I cannot wear it, it is two sizes too small.",
    ],
    ("product_quality", "negative"): [
        "The {product} started pilling after the first wash.",
        "A seam on the {product} came apart after two days.",
        "The fabric of the {product} feels cheap and thin.",
        "Colour of the {product} faded badly after one wash.",
        "The {product} arrived with a hole near the hem.",
    ],
    ("returns_refunds", "negative"): [
        "Returned the {product} three weeks ago and still no refund.",
        "The return process for the {product} was confusing and slow.",
        "I had to pay for shipping to return the {product}, not happy.",
        "Nobody confirmed that my returned {product} was received.",
        "Refund for the {product} was less than what I paid.",
    ],
    ("fit_sizing", "positive"): [
        "The {product} fits perfectly, true to size.",
        "Great cut, the {product} fits like it was made for me.",
        "Followed the size chart and the {product} fits just right.",
        "Love how the {product} fits, not too loose, not too tight.",
        "The {product} is true to size and very comfortable.",
    ],
    ("fit_sizing", "neutral"): [
        "The {product} fits okay, a bit loose around the waist.",
        "Fit of the {product} is fine, nothing special.",
        "The {product} is slightly long but wearable.",
        "Size is right but the {product} is cut a little boxy.",
        "The {product} fits as expected.",
    ],
    ("product_quality", "positive"): [
        "Lovely fabric, the {product} feels very well made.",
        "The {product} still looks new after many washes.",
        "Excellent stitching and quality on the {product}.",
        "The {product} is soft, thick and clearly built to last.",
        "Really impressed by the quality of the {product}.",
    ],
    ("product_quality", "neutral"): [
        "The {product} is decent quality for the price.",
        "Material of the {product} is okay, not premium.",
        "The {product} is fine, a little thinner than I expected.",
        "Quality of the {product} is average.",
        "The {product} does the job, nothing more.",
    ],
    ("other", "positive"): [
        "Fast delivery, the {product} arrived in two days.",
        "Beautiful colour, I get compliments every time I wear the {product}.",
        "Nice packaging and the {product} looks just like the photos.",
        "Great value, I will buy the {product} in another colour.",
        "Very happy with my {product}, thank you!",
    ],
    ("other", "neutral"): [
        "The {product} is okay.",
        "Delivery of the {product} took a bit longer than expected.",
        "The {product} looks slightly different from the photos.",
        "Bought the {product} as a gift, no complaints so far.",
        "The {product} is what I expected.",
    ],
}

# First customer turn of a chat, keyed by category. Always a complaint.
CHAT_OPENINGS = {
    "fit_sizing": [
        "Hi, the {product} I received is much smaller than the size chart says.",
        "Hello, the {product} is too tight even though I ordered my usual size.",
        "The sleeves of my {product} are far too short, what can I do?",
        "My {product} does not fit at all, the sizing seems off.",
        "Hi, I need help, the {product} is two sizes too small.",
    ],
    "product_quality": [
        "Hi, the zip on my {product} broke after a few days.",
        "Hello, my {product} has a hole in the fabric.",
        "The {product} lost its colour after the first wash.",
        "A seam on my {product} has already split.",
        "Hi, my {product} is pilling badly after one week.",
    ],
    "returns_refunds": [
        "Hi, I returned my {product} two weeks ago and have not been refunded.",
        "Hello, I cannot find how to start a return for my {product}.",
        "My refund for the {product} is missing part of the amount.",
        "I sent back the {product} but the tracking says nothing.",
        "Hi, why was I charged for returning the {product}?",
    ],
}

# Turns after the opening, in order; a chat uses the first 3-5 of them.
FOLLOW_UP_TURNS = [
    "Agent: I am sorry to hear that. Could you confirm your order number?",
    "Customer: Sure, it is in my confirmation email.",
    "Agent: Thank you, I can see your order for the {product}. I have passed this on to our team.",
    "Customer: Okay, how long will that take?",
    "Agent: You will receive an email with the next steps within two days.",
]
