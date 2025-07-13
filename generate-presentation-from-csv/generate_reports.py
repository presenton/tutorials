import os
import pandas as pd
import requests

os.makedirs('presentations', exist_ok=True)

df = pd.read_csv("students.csv")

def build_prompt(row):
    return (
        f"Student Name: {row['Name']}\n"
        f"Final Grade: {row['Final Grade']}\n"
        f"ECA Participation: {row['ECA Participation']}\n"
        f"Sports Involvement: {row['Sports Involvement']}\n"
        f"Quiz Scores: {row['Quiz Scores']}\n"
        f"Class Behavior: {row['Class Behavior']}\n"
        f"Teacher's Comment: {row['Comment']}\n\n"
        "Generate a parent-friendly presentation summarizing this student's academic and extracurricular performance, "
        "highlighting strengths, areas for improvement, and any special notes from the teacher."
    )

for idx, row in df.iterrows():
    print(f"Generating presentation for {row['Name']}")
    prompt = build_prompt(row)
    data = {
        "prompt": prompt,
        "n_slides": "8",
        "language": "English",
        "theme": "light",
        "export_as": "pdf"
    }
    response = requests.post(
        "http://localhost:5000/api/v1/ppt/generate/presentation",
        data=data
    )
    if response.ok:
        result = response.json()
        print("Downloading presentation...")
        # Prepend the host to the path
        download_url = f"http://localhost:5000{result['path']}"
        filename = f"presentations/{result['path'].split('/')[-1]}"
        # Download and save the file
        file_response = requests.get(download_url)
        if file_response.ok:
            with open(filename, 'wb') as f:
                f.write(file_response.content)
            print(f"Presentation for {row['Name']} saved as {filename}")
        else:
            print(f"Failed to download presentation for {row['Name']}: {file_response.status_code}")
    else:
        print(f"Failed to generate presentation for {row['Name']}: {response.text}")

