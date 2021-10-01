# waffle-rookies-19.5-backend-2 (assignment 3)

## test 과정에서 수정한 것들

* `PUT /api/v1/user/me/`  
response body에 `last_login` 항목이 누락되어 있어 추가했습니다.  
* `POST /api/v1/user/participant`  
성공 시의 status code가 `201`이 되어야 하는데 `200`으로 구현되어 있어서 수정했습니다.  
* seminar/views.py에 있던 복잡한 동작을 묶어서 seminar/services.py에 service layer로 구현했습니다.  
층이 더욱 세분화되다 보니 각 층에서 발생하는 return이나 raise(예외) 등을 어떻게 처리해야 할지가 좀 헷갈렸던 것 같습니다.

