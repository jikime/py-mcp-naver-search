import os
import httpx
import logging 
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv 
import json

from mcp.server.fastmcp import FastMCP

# --- 초기 설정 ---
# .env 파일 로드 (파일이 없어도 오류 발생 안 함)
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MCP 서버 인스턴스 생성
mcp = FastMCP("Naver Search MCP Server")
logger.info("Naver Search MCP Server 준비 중...")

# --- 네이버 API 설정 ---
NAVER_API_BASE_URL = "https://openapi.naver.com/v1/search/"
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
HEADERS = {}

if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
    HEADERS = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
else:
    logger.warning("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경 변수가 설정되지 않았습니다.")

# --- Pydantic 모델 정의 ---
# Optional 타입을 사용하여 필수값이 아닌 필드 명시
class BaseItem(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None

    class Config:
        extra = "ignore"

class DescriptionItem(BaseItem):
    description: Optional[str] = None

class BlogItem(DescriptionItem):
    bloggername: Optional[str] = None
    bloggerlink: Optional[str] = None
    postdate: Optional[str] = None

class NewsItem(DescriptionItem):
    originallink: Optional[str] = None
    pubDate: Optional[str] = None

class CafeArticleItem(DescriptionItem):
    cafename: Optional[str] = None
    cafeurl: Optional[str] = None

class KinItem(DescriptionItem):
    pass

WebkrItem = DescriptionItem
DocItem = DescriptionItem

class BookItem(BaseItem):
    image: Optional[str] = None
    author: Optional[str] = None
    price: Optional[str] = None
    discount: Optional[str] = None
    publisher: Optional[str] = None
    pubdate: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None

class ShopItem(BaseItem):
    image: Optional[str] = None
    lprice: Optional[str] = None
    hprice: Optional[str] = None
    mallName: Optional[str] = None
    productId: Optional[str] = None
    productType: Optional[str] = None
    maker: Optional[str] = None
    brand: Optional[str] = None
    category1: Optional[str] = None
    category2: Optional[str] = None
    category3: Optional[str] = None
    category4: Optional[str] = None

class ImageItem(BaseItem):
    thumbnail: Optional[str] = None
    sizeheight: Optional[str] = None
    sizewidth: Optional[str] = None

class LocalItem(BaseItem):
    category: Optional[str] = None
    description: Optional[str] = None
    telephone: Optional[str] = None
    address: Optional[str] = None
    roadAddress: Optional[str] = None
    mapx: Optional[str] = None
    mapy: Optional[str] = None

class EncycItem(BaseItem):
    thumbnail: Optional[str] = None
    description: Optional[str] = None

# 단일 결과 API 모델 (기존과 동일)
class AdultResult(BaseModel): adult: str
class ErrataResult(BaseModel): errata: str

# 검색 결과 공통 구조 (Optional 추가 및 기본값 설정)
class SearchResultBase(BaseModel):
    lastBuildDate: Optional[str] = None
    total: int = 0
    start: int = 1
    display: int = 10
    items: List[Any] = [] # 기본값 빈 리스트

# 각 API별 최종 응답 모델 정의
class BlogResult(SearchResultBase): items: List[BlogItem]
class NewsResult(SearchResultBase): items: List[NewsItem]
class CafeArticleResult(SearchResultBase): items: List[CafeArticleItem]
class KinResult(SearchResultBase): items: List[KinItem]
class WebkrResult(SearchResultBase): items: List[WebkrItem]
class DocResult(SearchResultBase): items: List[DocItem]
class BookResult(SearchResultBase): items: List[BookItem]
class ShopResult(SearchResultBase): items: List[ShopItem]
class ImageResult(SearchResultBase): items: List[ImageItem]
class LocalResult(SearchResultBase): items: List[LocalItem]
class EncycResult(SearchResultBase): items: List[EncycItem]

# 오류 응답 모델
class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    status_code: Optional[int] = None


# --- MCP Resource 정의 ---
@mcp.resource(
  uri='naver://available-search-categories', 
  name="available-search-categories", 
  description="Returns a list of Naver search categories available on this MCP server."
)
async def get_available_search_categories() -> List[str]:
    """Returns a list of Naver search categories available on this MCP server."""
    categories = [
        "blog", "news", "book", "adult", "encyc", "cafe_article",
        "kin", "local", "errata", "shop", "doc", "image", "webkr"
    ]
    logger.info(f"Resource 'get_available_search_categories' 호출됨. 반환: {categories}")
    return categories

# --- 네이버 API 호출 공통 함수 ---
async def _make_api_call(
    endpoint: str,
    params: Dict[str, Any],
    result_model: BaseModel,
    search_type_name: str # 동적 프롬프트 생성을 위한 검색 타입 이름 추가
) -> str:
    """
    Calls the Naver search API and parses the result, returning the result in text format.
    """
    if not HEADERS:
        logger.error("네이버 API 인증 정보가 설정되지 않았습니다.")
        error_resp = ErrorResponse(error="인증 정보 미설정", details="NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경 변수를 확인하세요.")
        return "오류 발생:\n" + f"오류: {error_resp.error}\n세부사항: {error_resp.details}"

    url = f"{NAVER_API_BASE_URL}{endpoint}"
    prompt_string = "처리 중 오류 발생:" # 기본 오류 프롬프트

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(f"네이버 API 호출 시작 - URL: {url}, Params: {params}")
            response = await client.get(url, headers=HEADERS, params=params)
            response.raise_for_status() # HTTP 오류 시 예외 발생

            data = response.json()
            logger.info(f"API 응답 성공 (상태 코드: {response.status_code})")

            try:
                # Pydantic 모델로 파싱 및 유효성 검사
                result = result_model.model_validate(data)
                logger.info(f"데이터 파싱 성공 (모델: {result_model.__name__})")

                # 동적 Prompt 생성 (SearchResultBase 상속 모델인 경우)
                if isinstance(result, SearchResultBase):
                    start_index = result.start
                    end_index = result.start + len(result.items) - 1
                    prompt_string = f"네이버 {search_type_name} 검색 결과 (총 {result.total:,}건 중 {start_index}~{end_index}번째):"
                    
                    # 결과를 구조화된 텍스트 형식으로 변환
                    text_result = f"{prompt_string}\n\n"
                    
                    # 결과 항목 형식화
                    for i, item in enumerate(result.items, 1):
                        text_result += f"### 결과 {i}\n"
                        
                        # 일반적인 항목 처리 (대부분의 모델에 공통)
                        if hasattr(item, 'title'):
                            # HTML 태그 제거
                            title = item.title.replace('<b>', '').replace('</b>', '')
                            text_result += f"제목(title): {title}\n"
                        
                        if hasattr(item, 'link'):
                            text_result += f"링크(link): {item.link}\n"
                        
                        if hasattr(item, 'description') and item.description:
                            # HTML 태그 제거
                            desc = item.description.replace('<b>', '').replace('</b>', '')
                            text_result += f"설명(description): {desc}\n"
                        
                        # 모델별 특수 필드 처리
                        if isinstance(item, BlogItem):
                            text_result += f"블로거명(bloggername): {item.bloggername}\n"
                            text_result += f"블로그 링크(bloggerlink): {item.bloggerlink}\n"
                            if item.postdate:
                                text_result += f"작성일(postdate): {item.postdate}\n"
                        
                        elif isinstance(item, NewsItem):
                            if item.originallink:
                                text_result += f"원본 링크(originallink): {item.originallink}\n"
                            if item.pubDate:
                                text_result += f"발행일(pubDate): {item.pubDate}\n"
                        
                        elif isinstance(item, BookItem) or isinstance(item, ShopItem):
                            if hasattr(item, 'image') and item.image:
                                text_result += f"이미지(image): {item.image}\n"
                            if hasattr(item, 'author') and item.author:
                                text_result += f"저자(author): {item.author}\n"
                            if hasattr(item, 'price') and item.price:
                                text_result += f"가격(price): {item.price}\n"
                            if hasattr(item, 'discount') and item.discount:
                                text_result += f"할인가(discount): {item.discount}\n"
                            if hasattr(item, 'publisher') and item.publisher:
                                text_result += f"출판사(publisher): {item.publisher}\n"
                            if hasattr(item, 'pubdate') and item.pubdate:
                                text_result += f"출판일(pubdate): {item.pubdate}\n"
                            if hasattr(item, 'isbn') and item.isbn:
                                text_result += f"ISBN(isbn): {item.isbn}\n"
                                
                        elif isinstance(item, ShopItem):
                            if hasattr(item, 'image') and item.image:
                                text_result += f"이미지(image): {item.image}\n"
                            if hasattr(item, 'lprice') and item.lprice:
                                text_result += f"최저가(lprice): {item.lprice}\n"
                            if hasattr(item, 'hprice') and item.hprice:
                                text_result += f"최고가(hprice): {item.hprice}\n"
                            if hasattr(item, 'mallName') and item.mallName:
                                text_result += f"쇼핑몰명(mallName): {item.mallName}\n"
                            if hasattr(item, 'brand') and item.brand:
                                text_result += f"브랜드(brand): {item.brand}\n"
                            if hasattr(item, 'maker') and item.maker:
                                text_result += f"제조사(maker): {item.maker}\n"
                            if hasattr(item, 'category1') and item.category1:
                                text_result += f"카테고리1(category1): {item.category1}\n"
                            if hasattr(item, 'category2') and item.category2:
                                text_result += f"카테고리2(category2): {item.category2}\n"
                            if hasattr(item, 'category3') and item.category3:
                                text_result += f"카테고리3(category3): {item.category3}\n"
                            if hasattr(item, 'category4') and item.category4:
                                text_result += f"카테고리4(category4): {item.category4}\n"
                                
                        elif isinstance(item, LocalItem):
                            if item.category:
                                text_result += f"카테고리(category): {item.category}\n"
                            if item.telephone:
                                text_result += f"전화번호(telephone): {item.telephone}\n"
                            if item.address:
                                text_result += f"주소(address): {item.address}\n"
                            if item.roadAddress:
                                text_result += f"도로명주소(roadAddress): {item.roadAddress}\n"
                            if item.mapx:
                                text_result += f"지도 X좌표(mapx): {item.mapx}\n"
                            if item.mapy:
                                text_result += f"지도 Y좌표(mapy): {item.mapy}\n"
                        
                        elif isinstance(item, ImageItem):
                            if item.thumbnail:
                                text_result += f"썸네일(thumbnail): {item.thumbnail}\n"
                            if item.sizeheight:
                                text_result += f"높이(sizeheight): {item.sizeheight}\n"
                            if item.sizewidth:
                                text_result += f"너비(sizewidth): {item.sizewidth}\n"
                        
                        elif isinstance(item, EncycItem):
                            if item.thumbnail:
                                text_result += f"썸네일(thumbnail): {item.thumbnail}\n"
                                
                        elif isinstance(item, CafeArticleItem):
                            if item.cafename:
                                text_result += f"카페명(cafename): {item.cafename}\n"
                            if item.cafeurl:
                                text_result += f"카페 링크(cafeurl): {item.cafeurl}\n"
                                
                        text_result += "\n"
                    
                    return text_result
                
                elif isinstance(result, AdultResult):
                    prompt_string = f"네이버 {search_type_name} 확인 결과:"
                    if result.adult == 0:
                        return f"{prompt_string} 일반 검색어"
                    else:
                        return f"{prompt_string} 성인 검색어"
                
                elif isinstance(result, ErrataResult):
                    print(f"ErrataResult: {result}")
                    prompt_string = f"네이버 {search_type_name} 확인 결과:"
                    if result.errata == "":
                        return f"{prompt_string} 오타 없음"
                    else:
                        return f"{prompt_string} {result.errata}"
                
                else: # 예상치 못한 결과 타입
                    prompt_string = f"네이버 {search_type_name} 처리 결과:"
                    # 결과를 JSON 형식의 문자열로 변환
                    result_json = json.dumps(result.model_dump(), ensure_ascii=False)
                    return f"{prompt_string}\n{result_json}"

            except ValidationError as e:
                logger.error(f"Pydantic 유효성 검사 오류: {e}")
                error_resp = ErrorResponse(error="응답 데이터 형식 오류", details=str(e))
                return f"{prompt_string}\n오류: {error_resp.error}\n세부사항: {error_resp.details}"

    except httpx.HTTPStatusError as e:
        logger.error(f"API HTTP 상태 오류: {e.response.status_code} - {e.response.text}", exc_info=True)
        error_resp = ErrorResponse(
            error=f"API 오류 ({e.response.status_code})",
            details=e.response.text,
            status_code=e.response.status_code
        )
        return f"{prompt_string}\n오류: {error_resp.error}\n세부사항: {error_resp.details}"
    except httpx.RequestError as e:
        logger.error(f"네트워크 요청 오류: {e}", exc_info=True)
        error_resp = ErrorResponse(error="네트워크 오류", details=f"네이버 API 서버 연결 실패: {e}")
        return f"{prompt_string}\n오류: {error_resp.error}\n세부사항: {error_resp.details}"
    except Exception as e:
        logger.exception(f"예상치 못한 오류 발생: {e}") # exc_info=True와 동일
        error_resp = ErrorResponse(error="서버 내부 오류", details=str(e))
        return f"{prompt_string}\n오류: {error_resp.error}\n세부사항: {error_resp.details}"


# --- 페이지 계산 함수 ---
def calculate_start(page: int, display: int) -> int:
    """Calculates the start value for the API call based on the page number and display count."""
    if page < 1:
        page = 1
    start = (page - 1) * display + 1
    # 네이버 API의 start 최대값(1000) 제한 고려
    return min(start, 1000)

# --- MCP Tool 정의 (페이지네이션, 동적 Prompt 적용) ---

# 1. 블로그 검색
@mcp.tool(
  name="search_blog",
  description="Searches for blogs on Naver using the given keyword. The page parameter allows for page navigation."
)
async def search_blog(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str:
    """
    Searches for blogs on Naver using the given keyword. The page parameter allows for page navigation.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): 정렬 기준. 기본값은 "sim" (유사도).
    """
    start = calculate_start(page, display)
    display = min(display, 100) # display 최대값 제한
    params = {"query": query, "display": display, "start": start, "sort": sort}
    return await _make_api_call("blog.json", params, BlogResult, "Blog")

# 2. 뉴스 검색
@mcp.tool(
  name="search_news",
  description="Searches for news on Naver using the given keyword. The page parameter allows for page navigation and sort='sim'/'date' is supported."
)
async def search_news(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str:
    """
    Searches for news on Naver using the given keyword. The page parameter allows for page navigation and sort='sim'/'date' is supported.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): The sorting criteria. Default is "sim" (similarity).
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start, "sort": sort}
    return await _make_api_call("news.json", params, NewsResult, "News")

# 3. 책 검색 (기본)
@mcp.tool(
  name="search_book",
  description="Searches for book information on Naver using the given keyword. The page parameter allows for page navigation."
)
async def search_book(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str:
    """
    Searches for book information on Naver using the given keyword. The page parameter allows for page navigation.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): The sorting criteria. Default is "sim" (similarity).
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start, "sort": sort}
    return await _make_api_call("book.json", params, BookResult, "Book")

# 4. 성인 검색어 판별 (페이지네이션 없음)
@mcp.tool(
  name="check_adult_query",
  description="Determines if the input query is an adult search term."
)
async def check_adult_query(query: str) -> str:
    """
    Determines if the input query is an adult search term.

    Args:
        query (str): The keyword to search for
    """
    params = {"query": query}
    return await _make_api_call("adult.json", params, AdultResult, "Adult Search Term")

# 5. 백과사전 검색
@mcp.tool(
  name="search_encyclopedia",
  description="Searches for encyclopedia information on Naver using the given keyword. The page parameter allows for page navigation."
)
async def search_encyclopedia(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str:
    """
    Searches for encyclopedia information on Naver using the given keyword. The page parameter allows for page navigation.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): The sorting criteria. Default is "sim" (similarity).
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start, "sort": sort}
    return await _make_api_call("encyc.json", params, EncycResult, "Encyclopedia")

# 6. 카페글 검색
@mcp.tool(
  name="search_cafe_article",
  description="Searches for cafe articles on Naver using the given keyword. The page parameter allows for page navigation and sort='sim'/'date' is supported."
)
async def search_cafe_article(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str:
    """
    Searches for cafe articles on Naver using the given keyword. The page parameter allows for page navigation and sort='sim'/'date' is supported.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): The sorting criteria. Default is "sim" (similarity).
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start, "sort": sort}
    return await _make_api_call("cafearticle.json", params, CafeArticleResult, "Cafe Article")

# 7. 지식iN 검색
@mcp.tool(
  name="search_kin",
  description="Searches for knowledgeiN Q&A on Naver using the given keyword. The page parameter allows for page navigation and sort='sim'/'date'/'point' is supported."
)
async def search_kin(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str:
    """
    Searches for knowledgeiN Q&A on Naver using the given keyword. The page parameter allows for page navigation and sort='sim'/'date'/'point' is supported.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): The sorting criteria. Default is "sim" (similarity).
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start, "sort": sort}
    return await _make_api_call("kin.json", params, KinResult, "KnowledgeiN")

# 8. 지역 검색 (페이지네이션 미지원 API)
@mcp.tool(
  name="search_local",
  description="Searches for local business information using the given keyword. (display maximum 5, start maximum 1) sort='random'/'comment' is supported."
)
async def search_local(query: str, display: int = 5, page: int = 1, sort: str = "random") -> str:
    """
    Searches for local business information using the given keyword. (display maximum 5, start maximum 1) sort='random'/'comment' is supported.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 5.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): The sorting criteria. Default is "random" (random).
    """
    display = min(display, 5) # API 제약 조건 적용
    start = 1  # 지역 API는 항상 start=1
    params = {"query": query, "display": display, "start": start, "sort": sort}
    return await _make_api_call("local.json", params, LocalResult, "Local")

# 9. 오타 변환 (페이지네이션 없음)
@mcp.tool(
  name="correct_errata",
  description="Converts Korean/English keyboard input errors."
)
async def correct_errata(query: str) -> str:
    """
    Converts Korean/English keyboard input errors.

    Args:
        query (str): The keyword to search for
    """
    params = {"query": query}
    return await _make_api_call("errata.json", params, ErrataResult, "Errata Conversion")

# 10. 쇼핑 검색
@mcp.tool(
  name="search_shop",
  description="Searches for shopping product information on Naver using the given keyword. The page parameter allows for page navigation and sort='sim'/'date'/'asc'/'dsc' is supported."
)
async def search_shop(query: str, display: int = 10, page: int = 1, sort: str = "sim") -> str:
    """
    Searches for shopping product information on Naver using the given keyword. The page parameter allows for page navigation and sort='sim'/'date'/'asc'/'dsc' is supported.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): The sorting criteria. Default is "sim" (similarity).
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start, "sort": sort}
    return await _make_api_call("shop.json", params, ShopResult, "Shopping")

# 11. 전문자료 검색
@mcp.tool(
  name="search_doc",
  description="Searches for academic papers, reports, etc. using the given keyword. The page parameter allows for page navigation."
)
async def search_doc(query: str, display: int = 10, page: int = 1) -> str:
    """
    Searches for academic papers, reports, etc. using the given keyword. The page parameter allows for page navigation.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start}
    return await _make_api_call("doc.json", params, DocResult, "Academic Papers")

# 12. 이미지 검색
@mcp.tool(
  name="search_image",
  description="Searches for images using the given keyword. The page parameter allows for page navigation and sort='sim'/'date', filter='all'/'large'/'medium'/'small' is supported."
)
async def search_image(query: str, display: int = 10, page: int = 1, sort: str = "sim", filter: str = "all") -> str:
    """
    Searches for images using the given keyword. The page parameter allows for page navigation and sort='sim'/'date', filter='all'/'large'/'medium'/'small' is supported.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
        sort (str, optional): The sorting criteria. Default is "sim" (similarity).
        filter (str, optional): The image size filter. Default is "all" (all sizes).
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start, "sort": sort, "filter": filter}
    return await _make_api_call("image.json", params, ImageResult, "Image")

# 13. 웹문서 검색
@mcp.tool(
  name="search_webkr",
  description="Searches for web documents using the given keyword. The page parameter allows for page navigation."
)
async def search_webkr(query: str, display: int = 10, page: int = 1) -> str:
    """
    Searches for web documents using the given keyword. The page parameter allows for page navigation.

    Args:
        query (str): The keyword to search for
        display (int, optional): The number of results to display. Default is 10.
        page (int, optional): The starting page number. Default is 1.
    """
    start = calculate_start(page, display)
    display = min(display, 100)
    params = {"query": query, "display": display, "start": start}
    return await _make_api_call("webkr.json", params, WebkrResult, "Web Document")


# --- 서버 실행 안내 ---
if __name__ == "__main__":
    # logger.info("-" * 30)
    # logger.info("MCP 서버를 실행하려면 터미널에서")
    # logger.info("다음 명령어를 입력하세요:")
    # logger.info(f"cd {os.path.basename(os.getcwd())}")
    # logger.info("mcp dev server.py")
    # logger.info("-" * 30)
    mcp.run()
