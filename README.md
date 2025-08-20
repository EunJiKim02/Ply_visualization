# Ply_visualization


### Function 
- Point cloud가 들어있는 폴더의 root 의 절대 경로 입력하면 자동으로 ply 파일 탐색
-  탐색된 ply 선택 가능
-  화면 기준으로 좌상단에 있는 ply 기준으로 뷰 정렬 (동기화 버튼 사용)
-  각 ply 에 카메라 버튼 누르면 png 저장 가능
-  검색 기능 지원 (경로 내부의 키워드까지 입력 가능)




### How to use

Suppported OS : Linux, Windows

1. Run the Python(Dash) program

```bash
python ply_visual.py
```

2. Open a web browser and go to localhost:8080.

3. Enter the Absolute path of your directory containing your PLY files.

    (Options) To filter the files, enter a keyword within your their names.

4. Click the 검색(search) button

5. Select the ply file you want to see.

    5-1. Click the 뷰초기화 button to You reset the viewpoint to its default setting

    5-2. Click the 첫번째뷰로정렬하기 button to synchronize the viewpoint of the selected point cloud with the first one displayed (the top-left view)


