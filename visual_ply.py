import os
import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ALL
import plotly.graph_objs as go
import open3d as o3d


# 🔹 PLY 로딩 함수
def load_ply_as_scatter(ply_path, name, marker_size=1):
    pcd = o3d.io.read_point_cloud(ply_path)
    pts = np.asarray(pcd.points)
    cols = np.asarray(pcd.colors)

    if cols.shape[0] != pts.shape[0]:
        cols = np.tile(np.array([[0.5, 0.5, 0.5]]), (pts.shape[0], 1))

    scatter = go.Scatter3d(
        x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
        mode="markers",
        marker=dict(size=marker_size, color=cols, opacity=0.8),
        name=name
    )
    return scatter


# 🔹 root 경로 안에서 모든 PLY 찾기
def find_ply_files(root):
    ply_files = []
    for parent, dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".ply"):
                ply_files.append(os.path.join(parent, f))
    return ply_files


def visualize_ply_app(marker_size_default=1, n_cols=3):
    app = dash.Dash(__name__, suppress_callback_exceptions=True)

    app.layout = html.Div([

        html.H2("Point Cloud Viewer (Dash)"),

        # 🔹 경로 입력 + 검색어 입력
        html.Div([
            dcc.Input(
                id="root-input",
                type="text",
                placeholder="폴더 경로 입력 (예: C:\\data 또는 /home/user/data)",
                style={"width": "50%", "marginRight": "10px"}
            ),
            dcc.Input(
                id="search-input",
                type="text",
                placeholder="파일/폴더 경로 검색 (예: chair, scene 등)",
                style={"width": "30%", "marginRight": "10px"}
            ),
            html.Button("검색", id="load-btn", n_clicks=0)
        ], style={"marginBottom": "15px"}),

        # 🔹 마커 크기 선택 슬라이더
        html.Div([
            html.Label("Marker size", style={"fontWeight": "bold", "marginRight": "12px"}),
            dcc.Slider(
                id="marker-size",
                min=1, max=5, step=0.5, value=marker_size_default,
                marks={i: str(i) for i in range(1, 6)},
                tooltip={"placement": "bottom", "always_visible": False},
                updatemode="mouseup"
            )
        ], style={"marginBottom": "12px"}),

        # 🔹 Dropdown + 로딩 마크
        dcc.Loading(
            type="circle",
            children=dcc.Dropdown(
                id="ply-dropdown",
                options=[],
                multi=True,
                placeholder="PLY 파일을 선택하세요",
                style={"marginBottom": "15px"}
            )
        ),

        html.Button("뷰 초기화", id="reset-btn", n_clicks=0),
        html.Button("첫 번째 뷰로 동기화", id="sync-btn", n_clicks=0),

        # 🔹 Grid container + 로딩 마크
        dcc.Loading(
            type="circle",
            fullscreen=False,
            children=html.Div(id="grid-container", children="⚡ 아직 로드된 데이터가 없습니다.")
        )
    ], style={"width": "95%", "margin": "auto"})

    # 🔹 경로 + 검색어 → PLY 검색
    @app.callback(
        Output("ply-dropdown", "options"),
        Output("ply-dropdown", "placeholder"),
        Input("load-btn", "n_clicks"),
        State("root-input", "value"),
        State("search-input", "value"),
        prevent_initial_call=True
    )
    def update_dropdown(n_clicks, root, keyword):
        if not root:
            return [], "경로를 입력하세요."
        if not os.path.exists(root):
            return [], f"잘못된 경로입니다: {root}"

        ply_files = find_ply_files(root)
        if not ply_files:
            return [], f"PLY 파일을 찾을 수 없습니다: {root}"

        # 🔹 검색어 필터링 (경로 전체에서 검색)
        if keyword:
            ply_files = [
                p for p in ply_files
                if keyword.lower() in os.path.relpath(p, root).lower()
            ]

        if not ply_files:
            return [], f"검색어 '{keyword}'에 해당하는 파일이 없습니다."

        return (
            [{"label": os.path.relpath(p, root), "value": p} for p in ply_files],
            f"{len(ply_files)}개의 PLY 파일 발견"
        )

    # 🔹 선택한 ply 파일들 → 그리드 표시
    @app.callback(
        Output("grid-container", "children"),
        Input("ply-dropdown", "value"),
        Input("reset-btn", "n_clicks"),
        Input("marker-size", "value"),
        State("root-input", "value"),
        prevent_initial_call=True
    )
    def update_grid(ply_paths, reset_clicks, marker_size, root):
        if not ply_paths:
            return html.Div("PLY 파일을 선택하세요.")

        figs = []
        for ply_path in ply_paths:
            title = os.path.relpath(ply_path, root) if root and os.path.exists(root) else os.path.basename(ply_path)

            scatter = load_ply_as_scatter(ply_path, name=title, marker_size=marker_size)
            fig = go.Figure(data=[scatter])
            fig.update_layout(
                scene=dict(
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    zaxis=dict(visible=False),
                    aspectmode="data"
                ),
                margin=dict(l=0, r=0, t=20, b=0),
                height=500,
                showlegend=False
            )
            figs.append(html.Div([
                html.Div(title, style={
                    "textAlign": "center", "fontWeight": "bold", "marginBottom": "5px", "wordBreak": "break-all"
                }),
                dcc.Loading(
                    type="circle",
                    children=dcc.Graph(
                        id={"type": "pc-graph", "parent": ply_path},
                        figure=fig,
                        style={"height": "500px"},
                        clear_on_unhover=True
                    )
                )
            ]))

        return html.Div(figs, style={
            "display": "grid",
            "gridTemplateColumns": f"repeat({n_cols}, 1fr)",
            "gap": "15px"
        })

    # 🔹 동기화 버튼 → 첫 번째 그래프 카메라 뷰 반영
    @app.callback(
        Output({"type": "pc-graph", "parent": ALL}, "figure"),
        Input("sync-btn", "n_clicks"),
        State({"type": "pc-graph", "parent": ALL}, "relayoutData"),
        State("ply-dropdown", "value"),
        State("marker-size", "value"),
        State("root-input", "value"),
        prevent_initial_call=True
    )
    def sync_cameras(n_clicks, relayouts, ply_paths, marker_size, root):
        if not ply_paths:
            return dash.no_update

        base_cam = None
        if relayouts and relayouts[0] and "scene.camera" in relayouts[0]:
            base_cam = relayouts[0]["scene.camera"]

        figs = []
        for i, ply_path in enumerate(ply_paths):
            title = os.path.relpath(ply_path, root) if root and os.path.exists(root) else os.path.basename(ply_path)

            scatter = load_ply_as_scatter(ply_path, name=title, marker_size=marker_size)
            fig = go.Figure(data=[scatter])
            fig.update_layout(
                scene=dict(
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    zaxis=dict(visible=False),
                    aspectmode="data"
                ),
                margin=dict(l=0, r=0, t=20, b=0),
                height=500,
                showlegend=False
            )
            if base_cam:
                fig.update_layout(scene_camera=base_cam)
            figs.append(fig)

        return figs

    app.run(debug=False, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    visualize_ply_app(marker_size_default=1, n_cols=3)
