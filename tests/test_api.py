import requests
import time

def test_generate():
    url = "http://127.0.0.1:8080/generate"
    payload = {"prompt": "A happy upbeat electronic loop with a catchy synth melody"}
    
    print(f"Sending request to {url}...")
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=180)
        end_time = time.time()
        
        print(f"Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print("\n--- Musical Brief ---")
            print(data.get('brief'))
            print("\n--- Generated Code ---")
            print(data.get('code'))
            print(f"\nMIDI available at: {data.get('midi_url')}")

        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Failed to connect: {e}")

def download_mp3():
        url = "http://127.0.0.1:8080/download/audio?format=mp3"
        print(f"Downloading MP3 from {url}...")
        response = requests.get(url)
        if response.status_code == 200:
            with open("generated_music.mp3", "wb") as f:
                f.write(response.content)
            print(f"Rendering MP3 now... (please wait)")
            time.sleep(5)  # Simulate rendering time
            print("MP3 downloaded successfully.")
            print(f"File saved as: generated_music.mp3")
        else:
            print(f"Failed to download MP3: {response.status_code}")

if __name__ == "__main__":
    test_generate()
    download_mp3()
