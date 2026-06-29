# Rerank API (v2)

POST https://api.cohere.com/v2/rerank
Content-Type: application/json

This endpoint takes in a query and a list of texts and produces an ordered array with each text assigned a relevance score.

Reference: https://docs.cohere.com/reference/rerank

## OpenAPI Specification

```yaml
openapi: 3.1.0
info:
  title: v2
  version: 1.0.0
paths:
  /v2/rerank:
    post:
      operationId: rerank
      summary: Rerank API (v2)
      description: >-
        This endpoint takes in a query and a list of texts and produces an
        ordered array with each text assigned a relevance score.
      tags:
        - subpackage_v2
      parameters:
        - name: Authorization
          in: header
          description: Bearer authentication
          required: true
          schema:
            type: string
        - name: X-Client-Name
          in: header
          description: |
            The name of the project that is making the request.
          required: false
          schema:
            type: string
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/v2_rerank_Response_200'
        '400':
          description: >
            This error is returned when the request is not well formed. This
            could be because:
              - JSON is invalid
              - The request is missing required fields
              - The request contains an invalid combination of fields
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestBadRequestError'
        '401':
          description: >
            This error indicates that the operation attempted to be performed is
            not allowed. This could be because:
              - The api token is invalid
              - The user does not have the necessary permissions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestUnauthorizedError'
        '403':
          description: >
            This error indicates that the operation attempted to be performed is
            not allowed. This could be because:
              - The api token is invalid
              - The user does not have the necessary permissions
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestForbiddenError'
        '404':
          description: >
            This error is returned when a resource is not found. This could be
            because:
              - The endpoint does not exist
              - The resource does not exist eg model id, dataset id
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestNotFoundError'
        '422':
          description: >
            This error is returned when the request is not well formed. This
            could be because:
              - JSON is invalid
              - The request is missing required fields
              - The request contains an invalid combination of fields
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestUnprocessableEntityError'
        '429':
          description: Too many requests
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestTooManyRequestsError'
        '498':
          description: >
            This error is returned when a request or response contains a
            deny-listed token.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestInvalidTokenError'
        '499':
          description: |
            This error is returned when a request is cancelled by the user.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestClientClosedRequestError'
        '500':
          description: >
            This error is returned when an uncategorised internal server error
            occurs.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestInternalServerError'
        '501':
          description: >
            This error is returned when the requested feature is not
            implemented.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestNotImplementedError'
        '503':
          description: >
            This error is returned when the service is unavailable. This could
            be due to:
              - Too many users trying to access the service at the same time
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestServiceUnavailableError'
        '504':
          description: >
            This error is returned when a request to the server times out. This
            could be due to:
              - An internal services taking too long to respond
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Rerankv2RequestGatewayTimeoutError'
      requestBody:
        description: ''
        content:
          application/json:
            schema:
              type: object
              properties:
                model:
                  type: string
                  description: The identifier of the model to use, eg `rerank-v3.5`.
                query:
                  type: string
                  description: The search query
                documents:
                  type: array
                  items:
                    type: string
                  description: >-
                    A list of texts that will be compared to the `query`.

                    For optimal performance we recommend against sending more
                    than 1,000 documents in a single request.


                    **Note**: long documents will automatically be truncated to
                    the value of `max_tokens_per_doc`.


                    **Note**: structured data should be formatted as YAML
                    strings for best performance.
                top_n:
                  type: integer
                  description: >-
                    Limits the number of returned rerank results to the
                    specified value. If not passed, all the rerank results will
                    be returned.
                max_tokens_per_doc:
                  type: integer
                  description: >-
                    Defaults to `4096`. Long documents will be automatically
                    truncated to the specified number of tokens.
                priority:
                  type: integer
                  default: 0
                  description: >-
                    Controls how early the request is handled. Lower numbers
                    indicate higher priority (default: 0, the highest). When the
                    system is under load, higher-priority requests are processed
                    first and are the least likely to be dropped.
              required:
                - model
                - query
                - documents
servers:
  - url: https://api.cohere.com
    description: production
components:
  schemas:
    V2RerankPostResponsesContentApplicationJsonSchemaResultsItems:
      type: object
      properties:
        index:
          type: integer
          description: >-
            Corresponds to the index in the original list of documents to which
            the ranked document belongs. (i.e. if the first value in the
            `results` object has an `index` value of 3, it means in the list of
            documents passed in, the document at `index=3` had the highest
            relevance)
        relevance_score:
          type: number
          format: double
          description: >-
            Relevance scores are normalized to be in the range `[0, 1]`. Scores
            close to `1` indicate a high relevance to the query, and scores
            closer to `0` indicate low relevance. It is not accurate to assume a
            score of 0.9 means the document is 2x more relevant than a document
            with a score of 0.45
      required:
        - index
        - relevance_score
      title: V2RerankPostResponsesContentApplicationJsonSchemaResultsItems
    ApiMetaApiVersion:
      type: object
      properties:
        version:
          type: string
        is_deprecated:
          type: boolean
        is_experimental:
          type: boolean
      required:
        - version
      title: ApiMetaApiVersion
    ApiMetaBilledUnits:
      type: object
      properties:
        images:
          type: number
          format: double
          description: |
            The number of billed images.
        input_tokens:
          type: number
          format: double
          description: |
            The number of billed input tokens.
        image_tokens:
          type: number
          format: double
          description: |
            The number of billed image tokens.
        output_tokens:
          type: number
          format: double
          description: |
            The number of billed output tokens.
        search_units:
          type: number
          format: double
          description: |
            The number of billed search units.
        classifications:
          type: number
          format: double
          description: |
            The number of billed classifications units.
      title: ApiMetaBilledUnits
    ApiMetaTokens:
      type: object
      properties:
        input_tokens:
          type: number
          format: double
          description: |
            The number of tokens used as input to the model.
        output_tokens:
          type: number
          format: double
          description: |
            The number of tokens produced by the model.
      title: ApiMetaTokens
    ApiMeta:
      type: object
      properties:
        api_version:
          $ref: '#/components/schemas/ApiMetaApiVersion'
        billed_units:
          $ref: '#/components/schemas/ApiMetaBilledUnits'
        tokens:
          $ref: '#/components/schemas/ApiMetaTokens'
        cached_tokens:
          type: number
          format: double
          description: |
            The number of prompt tokens that hit the inference cache.
        warnings:
          type: array
          items:
            type: string
      title: ApiMeta
    v2_rerank_Response_200:
      type: object
      properties:
        id:
          type: string
        results:
          type: array
          items:
            $ref: >-
              #/components/schemas/V2RerankPostResponsesContentApplicationJsonSchemaResultsItems
          description: An ordered list of ranked documents
        meta:
          $ref: '#/components/schemas/ApiMeta'
      required:
        - results
      title: v2_rerank_Response_200
    Rerankv2RequestBadRequestError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestBadRequestError
    Rerankv2RequestUnauthorizedError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestUnauthorizedError
    Rerankv2RequestForbiddenError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestForbiddenError
    Rerankv2RequestNotFoundError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestNotFoundError
    Rerankv2RequestUnprocessableEntityError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestUnprocessableEntityError
    Rerankv2RequestTooManyRequestsError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestTooManyRequestsError
    Rerankv2RequestInvalidTokenError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestInvalidTokenError
    Rerankv2RequestClientClosedRequestError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestClientClosedRequestError
    Rerankv2RequestInternalServerError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestInternalServerError
    Rerankv2RequestNotImplementedError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestNotImplementedError
    Rerankv2RequestServiceUnavailableError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestServiceUnavailableError
    Rerankv2RequestGatewayTimeoutError:
      type: object
      properties:
        message:
          type: string
        id:
          type: string
      title: Rerankv2RequestGatewayTimeoutError
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer

```

## Examples



**Request**

```json
{
  "model": "rerank-v4.0-pro",
  "query": "What is the capital of the United States?",
  "documents": [
    "Carson City is the capital city of the American state of Nevada.",
    "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
    "Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.",
    "Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.",
    "Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states."
  ],
  "top_n": 3
}
```

**Response**

```json
{
  "results": [
    {
      "index": 3,
      "relevance_score": 0.999071
    },
    {
      "index": 4,
      "relevance_score": 0.7867867
    },
    {
      "index": 0,
      "relevance_score": 0.32713068
    }
  ],
  "id": "07734bd2-2473-4f07-94e1-0d9f0e6843cf",
  "meta": {
    "api_version": {
      "version": "2",
      "is_experimental": false
    },
    "billed_units": {
      "search_units": 1
    }
  }
}
```

**SDK Code**

```typescript Cohere TypeScript SDK
import { CohereClient } from 'cohere-ai';

const cohere = new CohereClient({});

(async () => {
  const rerank = await cohere.v2.rerank({
    documents: [
      'Carson City is the capital city of the American state of Nevada.',
      'The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.',
      'Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.',
      'Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.',
      'Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.',
    ],
    query: 'What is the capital of the United States?',
    topN: 3,
    model: 'rerank-v4.0-pro',
  });

  console.log(rerank);
})();

```

```typescript
import { CohereClient } from "cohere-ai";

async function main() {
    const client = new CohereClient({
        token: "YOUR_TOKEN_HERE",
    });
    await client.v2.rerank({
        model: "rerank-v4.0-pro",
        query: "What is the capital of the United States?",
        documents: [
            "Carson City is the capital city of the American state of Nevada.",
            "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
            "Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.",
            "Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.",
            "Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.",
        ],
        topN: 3,
    });
}
main();

```

```python Sync
import cohere

co = cohere.ClientV2()

docs = [
    "Carson City is the capital city of the American state of Nevada.",
    "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
    "Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.",
    "Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.",
    "Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.",
]

response = co.rerank(
    model="rerank-v4.0-pro",
    query="What is the capital of the United States?",
    documents=docs,
    top_n=3,
)
print(response)

```

```python Async
import cohere
import asyncio

co = cohere.AsyncClientV2()

async def main():
    response = await co.rerank(
        model="rerank-v4.0-pro",
        query="What is the capital of the United States?",
        documents=[
            "Carson City is the capital city of the American state of Nevada.",
            "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
            "Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.",
            "Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.",
            "Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.",
        ],
        top_n=3
    )
    print(response)


asyncio.run(main())

```

```python
from cohere import Client

client = Client(
    token="YOUR_TOKEN_HERE",
)

client.v2.rerank(
    model="rerank-v4.0-pro",
    query="What is the capital of the United States?",
    documents=[
        "Carson City is the capital city of the American state of Nevada.",
        "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
        "Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.",
        "Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.",
        "Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states."
    ],
    top_n=3,
)

```

```java Cohere java SDK
/* (C)2024 */
import com.cohere.api.Cohere;
import com.cohere.api.resources.v2.requests.V2RerankRequest;
import com.cohere.api.resources.v2.types.V2RerankResponse;
import java.util.List;

public class RerankV2Post {
  public static void main(String[] args) {
    Cohere cohere = Cohere.builder().clientName("snippet").build();

    V2RerankResponse response =
        cohere
            .v2()
            .rerank(
                V2RerankRequest.builder()
                    .model("rerank-v4.0-pro")
                    .query("What is the capital of the United States?")
                    .documents(
                        List.of(
                            "Carson City is the capital city of the American state of Nevada.",
                            "The Commonwealth of the Northern Mariana Islands is a group of islands"
                                + " in the Pacific Ocean. Its capital is Saipan.",
                            "Capitalization or capitalisation in English grammar is the use of a"
                                + " capital letter at the start of a word. English usage varies"
                                + " from capitalization in other languages.",
                            "Washington, D.C. (also known as simply Washington or D.C., and"
                                + " officially as the District of Columbia) is the capital of the"
                                + " United States. It is a federal district.",
                            "Capital punishment has existed in the United States since before the"
                                + " United States was a country. As of 2017, capital punishment is"
                                + " legal in 30 of the 50 states."))
                    .topN(3)
                    .build());

    System.out.println(response);
  }
}

```

```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.cohere.com/v2/rerank"

	payload := strings.NewReader("{\n  \"model\": \"rerank-v4.0-pro\",\n  \"query\": \"What is the capital of the United States?\",\n  \"documents\": [\n    \"Carson City is the capital city of the American state of Nevada.\",\n    \"The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.\",\n    \"Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.\",\n    \"Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.\",\n    \"Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.\"\n  ],\n  \"top_n\": 3\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

```ruby
require 'uri'
require 'net/http'

url = URI("https://api.cohere.com/v2/rerank")

http = Net::HTTP.new(url.host, url.port)
http.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = 'Bearer <token>'
request["Content-Type"] = 'application/json'
request.body = "{\n  \"model\": \"rerank-v4.0-pro\",\n  \"query\": \"What is the capital of the United States?\",\n  \"documents\": [\n    \"Carson City is the capital city of the American state of Nevada.\",\n    \"The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.\",\n    \"Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.\",\n    \"Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.\",\n    \"Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.\"\n  ],\n  \"top_n\": 3\n}"

response = http.request(request)
puts response.read_body
```

```php
<?php
require_once('vendor/autoload.php');

$client = new \GuzzleHttp\Client();

$response = $client->request('POST', 'https://api.cohere.com/v2/rerank', [
  'body' => '{
  "model": "rerank-v4.0-pro",
  "query": "What is the capital of the United States?",
  "documents": [
    "Carson City is the capital city of the American state of Nevada.",
    "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
    "Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.",
    "Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.",
    "Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states."
  ],
  "top_n": 3
}',
  'headers' => [
    'Authorization' => 'Bearer <token>',
    'Content-Type' => 'application/json',
  ],
]);

echo $response->getBody();
```

```csharp
using RestSharp;

var client = new RestClient("https://api.cohere.com/v2/rerank");
var request = new RestRequest(Method.POST);
request.AddHeader("Authorization", "Bearer <token>");
request.AddHeader("Content-Type", "application/json");
request.AddParameter("application/json", "{\n  \"model\": \"rerank-v4.0-pro\",\n  \"query\": \"What is the capital of the United States?\",\n  \"documents\": [\n    \"Carson City is the capital city of the American state of Nevada.\",\n    \"The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.\",\n    \"Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.\",\n    \"Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.\",\n    \"Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states.\"\n  ],\n  \"top_n\": 3\n}", ParameterType.RequestBody);
IRestResponse response = client.Execute(request);
```

```swift
import Foundation

let headers = [
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
]
let parameters = [
  "model": "rerank-v4.0-pro",
  "query": "What is the capital of the United States?",
  "documents": ["Carson City is the capital city of the American state of Nevada.", "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.", "Capitalization or capitalisation in English grammar is the use of a capital letter at the start of a word. English usage varies from capitalization in other languages.", "Washington, D.C. (also known as simply Washington or D.C., and officially as the District of Columbia) is the capital of the United States. It is a federal district.", "Capital punishment has existed in the United States since beforethe United States was a country. As of 2017, capital punishment is legal in 30 of the 50 states."],
  "top_n": 3
] as [String : Any]

let postData = JSONSerialization.data(withJSONObject: parameters, options: [])

let request = NSMutableURLRequest(url: NSURL(string: "https://api.cohere.com/v2/rerank")! as URL,
                                        cachePolicy: .useProtocolCachePolicy,
                                    timeoutInterval: 10.0)
request.httpMethod = "POST"
request.allHTTPHeaderFields = headers
request.httpBody = postData as Data

let session = URLSession.shared
let dataTask = session.dataTask(with: request as URLRequest, completionHandler: { (data, response, error) -> Void in
  if (error != nil) {
    print(error as Any)
  } else {
    let httpResponse = response as? HTTPURLResponse
    print(httpResponse)
  }
})

dataTask.resume()
```