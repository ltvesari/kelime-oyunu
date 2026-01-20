# English Verb Card Game

This is a terminal-based spaced repetition game to help you learn English verbs, focusing on "Fitness" and "Daily Conversation" categories.

## How to Run

1.  Make sure you have Python installed.
2.  Open your terminal.
3.  Navigate to the directory containing `main.py`.
4.  Run the following command:
    ```bash
    python main.py
    ```

## Game Rules

- You will be presented with an English verb.
- Choose the correct Turkish translation from the 4 options.
- **Correct Answer**: The verb will appear less frequently (weight reduced by 50% after every 10 correct answers).
- **Incorrect Answer**: The verb will appear more frequently (weight increased by 50%).
- The game automatically saves your progress after each question.
- Enter `0` to save and exit.

## Adding More Verbs

To add more verbs (up to 1000+), edit the `verbs.json` file.
Add a new entry to the list in the following format:

```json
{
  "id": 51,
  "verb": "new verb",
  "turkish": "turkish meaning",
  "sentence": "Example sentence using the new verb.",
  "category": "Category Name",
  "weight": 100,
  "correct_count": 0
}
```

Make sure the `id` is unique!
