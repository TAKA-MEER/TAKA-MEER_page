// 昇降機の3Dビューア（盤の上を見る ページ）
// モデルは tools/cad/export_robot_glb.py で CAD から書き出した robot.glb。
// glb の中で stage1（1段目）と stage2（2段目、stage1 の子）が可動部になっている。
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const MODEL_URL = new URL('../models/robot.glb', import.meta.url);
const BOARD_HEIGHT = 3.0;        // 配電盤の目安（m）
const BOARD_GAP = 0.15;          // 機体と盤のすき間（m）
const ANIM_SECONDS = 2.5;        // 0→最大にかかる時間

const root = document.querySelector('[data-lift-viewer]');
if (root) init(root);

function init(root) {
  const canvas = root.querySelector('canvas');
  const range = root.querySelector('input[type="range"]');
  const button = root.querySelector('button');
  const heightOut = root.querySelector('[data-height]');
  const travelOut = root.querySelector('[data-travel]');
  const dateOut = root.querySelector('[data-model-date]');

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  } catch (e) {
    root.classList.add('is-unsupported');
    return;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  root.classList.add('is-ready', 'is-loading');
  range.disabled = button.disabled = true;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 50);
  camera.position.set(4.0, 3.0, 4.5);

  const controls = new OrbitControls(camera, canvas);
  controls.target.set(0, 1.9, -0.3);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 2;
  controls.maxDistance = 10;
  controls.maxPolarAngle = THREE.MathUtils.degToRad(85);
  controls.update();

  scene.add(new THREE.HemisphereLight(0xffffff, 0x888877, 2.2));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  sun.position.set(3, 6, 4);
  scene.add(sun);

  const env = buildEnvironment();
  scene.add(env.group);

  // 色はサイトの CSS 変数に合わせ、ダークモードの切り替えにも追従する（ロボットは CAD の色のまま）
  const applyTheme = () => {
    const css = getComputedStyle(document.documentElement);
    const c = (name) => new THREE.Color(css.getPropertyValue(name).trim());
    env.mat.floor.color = c('--panel-soft');
    env.mat.grid.color = c('--line');
    env.mat.board.color = c('--panel');
    env.mat.boardEdge.color = c('--muted');
    requestRender();
  };
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);

  // 昇降量 t（0〜1）。2段を同じ割合で伸ばす
  let robot = null;
  let t = 0;
  const setLift = (value) => {
    t = THREE.MathUtils.clamp(value, 0, 1);
    const [travel1, travel2] = robot.travel;
    robot.stage1.position.y = t * travel1;
    robot.stage2.position.y = t * travel2;
    range.value = Math.round(t * 100);
    heightOut.textContent = (robot.height + t * (travel1 + travel2)).toFixed(1);
    travelOut.textContent = (t * (travel1 + travel2)).toFixed(1);
    button.textContent = t >= 0.5 ? '下げる' : '上げる';
    requestRender();
  };

  new GLTFLoader().load(MODEL_URL.href, (gltf) => {
    const model = gltf.scene.getObjectByName('robot');
    const { travel, size, exported } = model.userData;
    robot = {
      stage1: model.getObjectByName('stage1'),
      stage2: model.getObjectByName('stage2'),
      travel,
      height: size[1],
    };
    scene.add(gltf.scene);
    env.board.position.z = -(size[2] / 2 + BOARD_GAP + env.boardDepth / 2);
    if (dateOut && exported) {
      const [y, m] = exported.split('-');
      dateOut.textContent = `${y}年${Number(m)}月`;
    }
    root.classList.remove('is-loading');
    range.disabled = button.disabled = false;
    setLift(0);
  }, undefined, () => {
    root.classList.remove('is-loading');
    root.classList.add('is-failed');
  });

  let anim = null;
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  range.addEventListener('input', () => {
    anim = null;
    setLift(range.value / 100);
  });
  button.addEventListener('click', () => {
    const to = t >= 0.5 ? 0 : 1;
    if (reduceMotion.matches) {
      setLift(to);
      return;
    }
    anim = { to, speed: 1 / ANIM_SECONDS };
    requestRender();
  });

  // 描画は必要なときだけ行う（スマホの電池を使いすぎない）
  let pending = false;
  let last = 0;
  function requestRender() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(frame);
  }
  function frame(now) {
    pending = false;
    const dt = last ? Math.min((now - last) / 1000, 0.1) : 0;
    last = now;
    if (anim) {
      const step = anim.speed * dt * Math.sign(anim.to - t);
      const next = Math.abs(anim.to - t) <= Math.abs(step) ? anim.to : t + step;
      setLift(next);
      if (next === anim.to) anim = null;
    }
    const moving = controls.update();
    renderer.render(scene, camera);
    if (anim || moving) requestRender();
    else last = 0;
  }
  controls.addEventListener('change', requestRender);

  let framed = false;
  new ResizeObserver(() => {
    const { clientWidth: w, clientHeight: h } = canvas;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    // 縦長（スマホ）では最初の視点を少し引き、伸びきった上端まで収める
    if (!framed) {
      framed = true;
      if (camera.aspect < 1) {
        camera.position.sub(controls.target).multiplyScalar(1.3).add(controls.target);
        controls.update();
      }
    }
    requestRender();
  }).observe(canvas);

  applyTheme();
}

// 床と、配電盤の目安（中身は描かない）
function buildEnvironment() {
  const mat = {
    floor: new THREE.MeshBasicMaterial(),
    grid: new THREE.LineBasicMaterial({ transparent: true, opacity: 0.6 }),
    board: new THREE.MeshStandardMaterial({ transparent: true, opacity: 0.18, depthWrite: false }),
    boardEdge: new THREE.LineBasicMaterial(),
  };
  const group = new THREE.Group();

  const floor = new THREE.Mesh(new THREE.CircleGeometry(4, 64), mat.floor);
  floor.rotation.x = -Math.PI / 2;
  group.add(floor);
  const grid = new THREE.GridHelper(8, 16);
  grid.material = mat.grid;
  grid.position.y = 0.001;
  group.add(grid);

  const boardDepth = 0.7;
  const boardGeo = new THREE.BoxGeometry(1.4, BOARD_HEIGHT, boardDepth);
  const board = new THREE.Mesh(boardGeo, mat.board);
  board.add(new THREE.LineSegments(new THREE.EdgesGeometry(boardGeo), mat.boardEdge));
  board.position.set(0, BOARD_HEIGHT / 2, -1);
  group.add(board);

  return { group, board, boardDepth, mat };
}
