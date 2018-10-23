# 아래 코드는 sequential download 코드
import collections
import requests
import tqdm

from flags2_common import main, save_flag, HTTPStatus, Result

DEFAULT_CONCUR_REQ = 1
MAX_CONCUR_REQ = 1

def get_flag(base_url, cc):
    url = '{}/{cc}/{cc}.gif'.format(base_url, cc=cc.lower())
    resp = requests.get(url)
    # 예외를 직접 처리하진 않는다
    # 그저 정상적이지 않으면 에러를 만들어 낼 뿐
    if resp.status_code != 200:
        resp.raise_for_status()
    return resp.content

def download_one(cc, base_url, verbose=False):
    try:
        image = get_flag(base_url, cc)
    except requests.exceptions.HTTPError as exc:
        res = exc.response
        # 404 에러만 처리
        if res.status_code == 404:
            status = HTTPStatus.not_found
            msg = 'not found'
        # 그 외의 에러는 호출자로 전달
        else:
            raise
    else:
        save_flag(image, cc.lower() + '.gif')
        status = HTTPStatus.ok
        msg = 'OK'
    
    if verbose:
        print(cc, msg)
    
    return Result(status, cc)

def download_many(cc_list, base_url, verbose, max_req):
    # HTTPStatus 별 합계를 각각 계산
    counter = collections.Counter()
    # 국가 코드 리스트 정렬
    cc_iter = sorted(cc_list)
    # 상세 메시지 모드가 아니면 tqdm 동작
    if not verbose:
        cc_iter = tqdm.tqdm(cc_iter)
    # 각 대상 돌리는 루프
    for cc in cc_iter:
        try:
            res = download_one(cc, base_url, verbose)
        # download_one()이 처리하지 못한 예외를 여기서 처리
        except requests.exceptions.HTTPError as exc:
            error_msg = 'HTTP error {res.status_code} - {res.reason}' 
            error_msg = error_msg.format(res=exc.response)
        # Network Connection 관련 error 처리
        except requests.exceptions.ConnectionError as exc:
            error_msg = 'Connection error'
        else:
            error_msg = ''
            status = res.status

        if error_msg:
            status = HTTPStatus.error
        # 각 상태별 카운터 증가
        counter[status] += 1
        # 상세 메시지 모드에서의 에러 출력
        if verbose and error_msg:
            print('*** Error for {}: {}'.format(cc, error_msg))
    
    return counter

if __name__ == '__main__':
    main(download_many, DEFAULT_CONCUR_REQ, MAX_CONCUR_REQ)