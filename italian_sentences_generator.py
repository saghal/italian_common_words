import re
import json
import time
import requests
from typing import List, Dict, Tuple, Optional

# Configuration
OPENROUTER_API_KEY = "PUT YOUR OWN KEY"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "deepseek/deepseek-chat"  

def parse_word_list(file_path: str) -> List[Dict]:
    """Parse the original word list file and extract words with their definitions."""
    words = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Pattern to match numbered entries like "1. il [article] - the"
    pattern = r'\d+\.\s+(\w+)\s+\[([^\]]+)\]\s+-\s+(.+)'
    matches = re.findall(pattern, content)
    
    for match in matches:
        word, word_type, translation = match
        words.append({
            'word': word.strip(),
            'type': word_type.strip(),
            'translation': translation.strip()
        })
    
    return words

def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters for most languages)."""
    return len(text) // 3  # Conservative estimate

def create_batch_prompt(word_batch: List[Dict]) -> str:
    """Create a batch prompt for multiple words with enhanced verb handling."""
    
    words_info = []
    verb_count = 0
    
    for i, word_data in enumerate(word_batch, 1):
        word_type = word_data['type']
        if word_type == 'verb':
            verb_count += 1
        words_info.append(f"{i}. {word_data['word']} [{word_data['type']}] = {word_data['translation']}")
    
    words_list = "\n".join(words_info)
    
    # Enhanced instructions for verbs
    verb_instructions = ""
    if verb_count > 0:
        verb_instructions = f"""
SPECIAL INSTRUCTIONS FOR VERBS ({verb_count} verbs in this batch):
- Use different subjects: io, tu, lei/lui, noi, voi, loro
- Show different conjugations naturally: presente, passato prossimo
- Examples for "essere": "Sono felice", "Lei è italiana", "Siamo amici"
- Examples for "avere": "Ho fame", "Hai una macchina", "Abbiamo tempo"  
- Examples for "fare": "Faccio colazione", "Cosa fai?", "Facciamo sport"
- Use verbs in real actions, not abstract concepts"""

    prompt = f"""You are an expert Italian teacher. Create exactly 5 natural A2-level Italian sentences for EACH word below.

WORDS TO PROCESS:
{words_list}

REQUIREMENTS FOR ALL WORDS:
- A2 CEFR level: simple vocabulary, basic grammar, everyday situations
- Each sentence MUST naturally contain the target word (not about studying it)
- Show words in different real contexts: family, food, work, daily life, hobbies
- 6-12 words per sentence maximum
- Use simple present tense primarily
- Each sentence should be completely different
- Perfect Italian grammar and natural usage{verb_instructions}

CRITICAL: Return EXACTLY this JSON structure with NO extra text:
{{
  "vocabulary": [
    {{
      "word": "{word_batch[0]['word']}",
      "examples": [
        {{"italian": "natural sentence with {word_batch[0]['word']}", "english": "English translation"}},
        {{"italian": "different sentence with {word_batch[0]['word']}", "english": "English translation"}},
        {{"italian": "another sentence with {word_batch[0]['word']}", "english": "English translation"}},
        {{"italian": "fourth sentence with {word_batch[0]['word']}", "english": "English translation"}},
        {{"italian": "fifth sentence with {word_batch[0]['word']}", "english": "English translation"}}
      ]
    }}{','.join([f'''
    {{
      "word": "{wd['word']}",
      "examples": [
        {{"italian": "natural sentence with {wd['word']}", "english": "English translation"}},
        {{"italian": "different sentence with {wd['word']}", "english": "English translation"}},
        {{"italian": "another sentence with {wd['word']}", "english": "English translation"}},
        {{"italian": "fourth sentence with {wd['word']}", "english": "English translation"}},
        {{"italian": "fifth sentence with {wd['word']}", "english": "English translation"}}
      ]
    }}''' for wd in word_batch[1:]])}
  ]
}}"""
    
    return prompt

def calculate_optimal_batch_size(words: List[Dict]) -> int:
    """Calculate optimal batch size based on token limitations."""

    MAX_INPUT_TOKENS = 6000  # Conservative limit
    PROMPT_OVERHEAD = 500
    TOKENS_PER_WORD_INPUT = 50
    TOKENS_PER_WORD_OUTPUT = 300
    
    # Calculate max words that fit in token limit
    available_tokens = MAX_INPUT_TOKENS - PROMPT_OVERHEAD
    max_words_input = available_tokens // TOKENS_PER_WORD_INPUT
    
    # Also consider output token limit
    MAX_OUTPUT_TOKENS = 4000
    max_words_output = MAX_OUTPUT_TOKENS // TOKENS_PER_WORD_OUTPUT
    
    # Take the minimum and add some buffer
    optimal_batch = min(max_words_input, max_words_output, 15)  # Cap at 15 words
    
    print(f"📊 Calculated optimal batch size: {optimal_batch} words per request")
    return max(1, optimal_batch)

def process_word_batch(word_batch: List[Dict], batch_num: int, total_batches: int) -> Optional[Dict]:
    """Process a batch of words in a single API call using OpenRouter."""
    
    batch_words = [wd['word'] for wd in word_batch]
    print(f"\n📦 Batch {batch_num}/{total_batches}: Processing {len(word_batch)} words")
    print(f"   Words: {', '.join(batch_words)}")
    
    prompt = create_batch_prompt(word_batch)
    
    # Estimate prompt size
    prompt_tokens = estimate_tokens(prompt)
    expected_response_tokens = len(word_batch) * 300
    print(f"   📏 Estimated tokens: {prompt_tokens} input + {expected_response_tokens} output = {prompt_tokens + expected_response_tokens}")
    
    # API call configuration
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            print(f"   🧠 DeepSeek API call via OpenRouter (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://italian-vocab-generator.app",  
                    "X-Title": "Italian Vocabulary Generator" 
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert Italian teacher. Generate perfect A2-level Italian sentences with natural grammar. Always return valid JSON with the exact structure requested."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.8,
                    "max_tokens": min(4000, expected_response_tokens + 500),
                    "top_p": 0.95
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Parse the batch response
                parsed_batch = parse_batch_response(content, word_batch)
                
                if parsed_batch:
                    successful_words = len([w for w in parsed_batch if parsed_batch[w]])
                    print(f"   ✅ SUCCESS: Generated examples for {successful_words}/{len(word_batch)} words")
                    return parsed_batch
                else:
                    print(f"   ⚠️  Failed to parse batch response, retrying...")
                    
            elif response.status_code == 429:
                wait_time = (attempt + 1) * 10
                print(f"   ⏰ Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            elif response.status_code == 402:
                print(f"   💳 Payment required - check OpenRouter credits at https://openrouter.ai/credits")
                return None
                
            else:
                error_detail = response.text[:200] if response.text else "No error details"
                print(f"   ❌ API error {response.status_code}: {error_detail}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timeout (attempt {attempt + 1})")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(5)
    
    print(f"   FAILED: Could not process batch after {max_retries} attempts")
    return None

def parse_batch_response(content: str, word_batch: List[Dict]) -> Optional[Dict]:
    """Parse batch response with minimal validation - trust the AI."""
    
    # Clean the content
    content = re.sub(r'```json\s*', '', content)
    content = re.sub(r'```\s*', '', content)
    content = content.strip()
    
    # Debug: Print first part of response
    print(f"   Response preview: {content[:200]}...")
    
    try:
        # Find and extract JSON
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_content = content[json_start:json_end]
        elif '[' in content and ']' in content:
            array_start = content.find('[')
            array_end = content.rfind(']') + 1
            if array_start >= 0 and array_end > array_start:
                array_content = content[array_start:array_end]
                json_content = f'{{"vocabulary": {array_content}}}'
        else:
            print(f"   ❌ No valid JSON structure found")
            return None
            
        parsed = json.loads(json_content)
        result = {}
        
        if "vocabulary" in parsed:
            vocab_list = parsed["vocabulary"]
            
            for word_entry in vocab_list:
                if "word" in word_entry and "examples" in word_entry:
                    word = word_entry["word"]
                    examples = word_entry["examples"]
                    
                    # Minimal validation
                    validated_examples = []
                    for ex in examples:
                        if isinstance(ex, dict) and "italian" in ex and "english" in ex:
                            italian = ex["italian"].strip()
                            english = ex["english"].strip()
                            
                            if (italian and english and 
                                len(italian.split()) >= 2 and
                                len(italian) > 5 and
                                not is_obviously_broken(italian)):
                                validated_examples.append((italian, english))
                    
                    if len(validated_examples) >= 3:
                        result[word] = validated_examples[:5]
                        print(f"   ✅ '{word}': {len(validated_examples)} examples accepted")
                    else:
                        result[word] = None
                        print(f"   ⚠️  '{word}': Only {len(validated_examples)} valid examples")
                        
        return result if result else None
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parsing error: {e}")
        print(f"   Raw content: {content[:500]}...")
        
        try:
            fixed_content = fix_json_issues(content)
            if fixed_content != content:
                print(f"   🔧 Attempting JSON repair...")
                return parse_batch_response(fixed_content, word_batch)
        except:
            pass
        
    except Exception as e:
        print(f"   ❌ Parsing error: {e}")
    
    return None

def is_obviously_broken(sentence: str) -> bool:
    """Only reject obviously broken sentences."""
    problems = [
        len(sentence) < 6,
        sentence.count('"') > 2,
        'ERROR' in sentence.upper(),
        sentence.startswith('[') and sentence.endswith(']'),
        sentence.count('.') > 3,
        not any(c.isalpha() for c in sentence)
    ]
    return any(problems)

def fix_json_issues(content: str) -> str:
    """Attempt to fix common JSON formatting issues."""
    # Remove trailing commas
    content = re.sub(r',\s*}', '}', content)
    content = re.sub(r',\s*]', ']', content)
    
    # Ensure proper closing
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces > close_braces:
        content += '}' * (open_braces - close_braces)
    
    return content

def create_vocabulary_file_batch(words: List[Dict], output_path: str):
    """Create vocabulary file using batch processing."""
    
    # Calculate optimal batch size
    batch_size = calculate_optimal_batch_size(words)
    
    # Split words into batches
    batches = [words[i:i + batch_size] for i in range(0, len(words), batch_size)]
    total_batches = len(batches)
    
    print(f"\n🚀 Starting BATCH AI generation with DeepSeek via OpenRouter")
    print(f"📦 {len(words)} words split into {total_batches} batches of ~{batch_size} words each")
    print(f"⚡ This is {len(words)//total_batches}x more efficient than individual requests!")
    print("-" * 80)
    
    successful_words = 0
    failed_words = 0
    total_sentences = 0
    
    with open(output_path, 'w', encoding='utf-8') as file:
        for batch_num, batch in enumerate(batches, 1):
            batch_results = process_word_batch(batch, batch_num, total_batches)
            
            if batch_results:
                for word_data in batch:
                    word = word_data['word']
                    word_type = word_data['type']
                    translation = word_data['translation']
                    
                    # Write word header
                    file.write(f"{word} [{word_type}] - {translation}\n")
                    
                    if word in batch_results and batch_results[word]:
                        examples = batch_results[word]
                        successful_words += 1
                        total_sentences += len(examples)
                        
                        # Write examples
                        for italian, english in examples:
                            file.write(f"{italian}\n")
                            file.write(f"{english}\n\n")
                    else:
                        failed_words += 1
                        file.write(f"[ERROR: Could not generate AI examples for '{word}']\n\n")
                    
                    # Add spacing between words
                    file.write("\n")
            else:
                # Entire batch failed
                for word_data in batch:
                    word = word_data['word']
                    word_type = word_data['type']
                    translation = word_data['translation']
                    failed_words += 1
                    
                    file.write(f"{word} [{word_type}] - {translation}\n")
                    file.write(f"[ERROR: Batch processing failed for '{word}']\n\n")
            
            # Rate limiting between batches
            if batch_num < total_batches:
                print(f"   🕐 Waiting 3 seconds before next batch...")
                time.sleep(3)
    
    # Final statistics
    print(f"\n" + "="*80)
    print(f"🎯 BATCH AI GENERATION COMPLETE!")
    print(f"📦 Processed {total_batches} batches")
    print(f"✅ Successfully generated: {successful_words} words ({successful_words/len(words)*100:.1f}%)")
    print(f"❌ Failed to generate: {failed_words} words ({failed_words/len(words)*100:.1f}%)")
    print(f"📊 Total AI sentences: {total_sentences}")
    print(f"⚡ Efficiency: {len(words)/total_batches:.1f} words per API call")
    print(f"💰 API calls used: {total_batches} (vs {len(words)} individual calls)")
    print(f"📁 Output: '{output_path}'")

def test_api_connection():
    """Test the OpenRouter API connection."""
    print(f"\n🔑 Testing OpenRouter API connection...")
    
    try:
        test_response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": "Say 'OK' if you can read this."}],
                "max_tokens": 10
            },
            timeout=15
        )
        
        if test_response.status_code == 200:
            print("✅ API connection successful!")
            return True
        elif test_response.status_code == 401:
            print("❌ Authentication failed - check your API key")
            return False
        elif test_response.status_code == 429:
            print("⚠️  Currently rate limited, but will proceed with batch processing")
            return True
        elif test_response.status_code == 402:
            print("❌ Payment required - add credits at https://openrouter.ai/credits")
            return False
        else:
            print(f"⚠️  API status {test_response.status_code}: {test_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main function for batch AI-generated Italian vocabulary."""
    
    print("🇮🇹 BATCH AI ITALIAN VOCABULARY GENERATOR")
    print("🚀 Multiple Words Per Request - Super Efficient!")
    print("🧠 100% AI Generated via OpenRouter")
    print("⚡ Smart Batching to Avoid Rate Limits")
    print("=" * 80)
    
    # Configuration
    input_file = "./data/italian_1112_words.txt"
    output_file = "italian_vocabulary_with_examples.txt"
    
    # Test API connection
    if not test_api_connection():
        print("\n⚠️  API test failed, but you can try to continue anyway.")
        proceed = input("Continue? (y/n): ").strip().lower()
        if proceed != 'y':
            return
    
    try:
        # Load words
        print(f"\n📖 Loading words from '{input_file}'...")
        words = parse_word_list(input_file)
        print(f"✅ Found {len(words)} words")
        
        # User selection
        choice = input(f"\nProcess how many words? (1-{len(words)} or 'all'): ").strip().lower()
        
        if choice != 'all':
            try:
                num_words = int(choice)
                if 1 <= num_words <= len(words):
                    words = words[:num_words]
                    print(f"✅ Processing first {len(words)} words")
            except ValueError:
                print("Invalid input. Processing all words.")
        
        # Show efficiency gains
        estimated_batches = max(1, len(words) // calculate_optimal_batch_size(words))
        print(f"\n📊 Batch Processing Benefits:")
        print(f"🔥 Individual requests: {len(words)} API calls")
        print(f"⚡ Batch requests: ~{estimated_batches} API calls")
        print(f"🚀 Efficiency gain: {len(words)/estimated_batches:.1f}x faster!")
        print(f"💰 Rate limit friendly: {estimated_batches} requests vs {len(words)}")
        
        confirm = input(f"\n🚀 Start batch generation? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Generation cancelled.")
            return
        
        # Generate vocabulary file using batches
        create_vocabulary_file_batch(words, output_file)
        
        print(f"\n🎉 BATCH PROCESSING COMPLETE!")
        print(f"📄 Generated vocabulary saved to: '{output_file}'")
        print(f"🧠 Powered by DeepSeek via OpenRouter")
        print(f"⚡ Maximum efficiency achieved!")
        
    except FileNotFoundError:
        print(f"\n❌ File '{input_file}' not found")
        print("📝 Expected format: '1. il [article] - the'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()