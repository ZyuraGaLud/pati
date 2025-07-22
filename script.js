// Canvasのセットアップ
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const SCREEN_WIDTH = canvas.width;
const SCREEN_HEIGHT = canvas.height;
const BALL_RADIUS = 5; // Pythonの定数と合わせる
const PIN_RADIUS = 4;  // Pythonの定数と合わせる
const POCKET_WIDTH = 80; // Pythonの定数と合わせる
const POCKET_HEIGHT = 20; // Pythonの定数と合わせる

// スコア表示要素
const scoreDisplay = document.getElementById('scoreDisplay');

let pyodide; // Pyodideインスタンス
let gameLogicModule; // Pythonのgame_logicモジュール

let lastFrameTime = 0; // 最後にフレームが描画された時間

// Pyodideの初期化
async function initializePyodide() {
    console.log("Pyodideを初期化中...");
    pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    // 必要であれば、追加のPythonパッケージをインストール
    // await pyodide.runPythonAsync(`
    //     import micropip
    //     await micropip.install('numpy')
    // `);

    // game_logic.pyファイルをPyodideに読み込む
    const pythonCode = await fetch('game_logic.py').then(response => response.text());
    pyodide.FS.writeFile("game_logic.py", pythonCode);
    gameLogicModule = pyodide.pyimport("game_logic");

    // Pythonの初期化関数を呼び出す
    const initialState = gameLogicModule.init_game_logic().toJs(); // PythonのDictをJavaScriptのMapに変換
    updateGameFromPython(initialState); // 初期状態をJavaScript側に反映

    console.log("Pyodide初期化完了！");
    gameLoop(0); // ゲームループを開始
}

// Pythonのゲーム状態をJavaScriptに反映
let currentGameState = {}; // 現在のゲーム状態を保持
function updateGameFromPython(pythonGameState) {
    currentGameState = {
        score: pythonGameState.get("score"),
        balls: pythonGameState.get("balls").toJs(), // PyListをJS Arrayに変換
        pins: pythonGameState.get("pins").toJs(),   // PyListをJS Arrayに変換
        pockets: pythonGameState.get("pockets").toJs(), // PyListをJS Arrayに変換
        game_status: pythonGameState.get("game_status"),
        big_win_start_time: pythonGameState.get("big_win_start_time"),
        current_big_win_message: pythonGameState.get("current_big_win_message"),
        rainbow_hue: pythonGameState.get("rainbow_hue")
    };
}


// ゲームループ
function gameLoop(currentTime) {
    const deltaTime = currentTime - lastFrameTime; // デルタタイム計算
    lastFrameTime = currentTime;

    // Pythonのゲームロジックを更新
    if (gameLogicModule) {
        // 現在のJavaScriptの時間をPythonに渡す
        const updatedState = gameLogicModule.update_game_state(deltaTime, currentTime).toJs();
        updateGameFromPython(updatedState);
    }

    drawGame(); // 描画
    requestAnimationFrame(gameLoop); // 次のフレームを要求
}

// 描画関数
function drawGame() {
    // 背景の描画
    if (currentGameState.game_status === "BIG_WIN") {
        // 虹色背景
        const h = currentGameState.rainbow_hue * 360; // 0-360度に変換
        ctx.fillStyle = `hsl(${h}, 100%, 50%)`; // HSL (Hue, Saturation, Lightness)
        ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
    } else {
        ctx.fillStyle = 'black';
        ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
    }

    // ピンの描画
    ctx.fillStyle = 'blue';
    currentGameState.pins.forEach(pin => {
        const [x, y] = pin;
        ctx.beginPath();
        ctx.arc(x, y, PIN_RADIUS, 0, Math.PI * 2);
        ctx.fill();
    });

    // ポケットの描画
    currentGameState.pockets.forEach(pocket => {
        const [x, y, width, height, is_big_win_pocket] = pocket;
        ctx.fillStyle = is_big_win_pocket ? 'green' : 'red';
        ctx.fillRect(x, y, width, height);
    });

    // 玉の描画
    ctx.fillStyle = 'white';
    currentGameState.balls.forEach(ball => {
        const [x, y, _] = ball; // x, y のみ使用
        ctx.beginPath();
        ctx.arc(x, y, BALL_RADIUS, 0, Math.PI * 2);
        ctx.fill();
    });

    // スコア表示
    scoreDisplay.textContent = currentGameState.score;

    // 大当たりメッセージ
    if (currentGameState.game_status === "BIG_WIN") {
        ctx.font = 'bold 72px Arial';
        ctx.fillStyle = 'black'; // メッセージは黒字に
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(currentGameState.current_big_win_message, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2);
    }
}

// キーボードイベントリスナー
document.addEventListener('keydown', (event) => {
    if (event.code === 'Space') {
        if (gameLogicModule) {
            gameLogicModule.add_ball(); // Pythonのadd_ball関数を呼び出す
        }
    }
});

// Pyodideの初期化を開始
initializePyodide();