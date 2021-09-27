# waffle-rookies-19.5-backend-2

## 과제 11번 Debug Toolbar 관련

![image](https://user-images.githubusercontent.com/84006386/134805703-7c0bf894-66a6-4d60-8cdd-badaa236a2f9.png)

`/api/v1/seminar/`에 접속해서 Debug Toolbar를 실행해보았더니 사진처럼 중복된 query가 25개나 있다고 나왔습니다.
각 query의 출처를 살펴보니 주로 모델 객체의 field를 참조할 때마다 query가 발생하는 것 같던데,
어떻게 해야 불필요한 중복을 피하면서 원래 기능을 유지할 수 있을지 고민을 해보았지만 방법을 찾지 못헀습니다ㅠ

그리고 잘 이해가 되지 않는 부분도 있었습니다.
세미나 중 QuerySet의 특징이 caching을 통해 같은 query가 여러 번 들어왔을 때 굳이 번번이 DB를 참조하지 않는 것이라고 하셨는데,
중복된 query라는 건 어떻게 발생하게 되는 건가요?
caching 된 내용을 이용하고 DB를 직접 참조하지 않은 query도 '중복'으로 카운트가 되는 건가요?

다음 세미나 때 기회가 된다면 query 중복을 피할 수 있는 요령에 대해 살짝 알려주셨으면 좋겠습니다!

매번 고생 많으십니다 감사합니다 :)