<template>
  <section class="story-stage" :class="{ flat: flat || failed }">
    <div class="stage-toolbar">
      <div>
        <span class="live-dot" :class="{ playing }"></span
        ><b>{{ sceneLabel }}剧场</b
        ><small>{{ flat || failed ? "平面演绎" : "3D 实时场景" }}</small>
      </div>
      <div class="stage-buttons">
        <button
          @click="playing ? stop() : play(activeIndex)"
          :disabled="!dialogues.length"
          :aria-label="playing ? '暂停演绎' : '播放角色对白'"
        >
          {{ playing ? "Ⅱ 暂停" : "▷ 播放对白" }}
        </button>
        <button @click="flat = !flat" :aria-pressed="flat || failed" :disabled="failed">
          {{ failed ? "平面兼容模式" : flat ? "切换三维" : "平面模式" }}
        </button>
      </div>
    </div>
    <div
      class="stage-canvas"
      ref="host"
      aria-label="点击人物可选为对话对象并播放其字幕的三维剧场"
    ></div>
    <div v-if="flat || failed" class="flat-scene" :class="sceneType">
      <div class="flat-window"></div>
      <div class="flat-board"></div>
      <div class="flat-floor"></div>
      <div
        v-for="(role, i) in roles.slice(0, 4)"
        :key="role.name"
        class="flat-person"
        :class="{ talking: playing && speakerIndex === i }"
        :style="{
          left: `${18 + i * 21}%`,
          '--shirt': outfits[i % outfits.length],
        }"
      >
        <div class="flat-head"><i></i><i></i><span></span></div>
        <div class="flat-body"></div>
        <div class="flat-legs"></div>
        <strong>{{ role.name }}</strong>
      </div>
    </div>
    <div v-if="!ready && !flat && !failed" class="stage-loading">
      正在布置三维场景…
    </div>
    <div class="stage-subtitles" :class="{ active: playing }">
      <span>{{ activeDialogue?.name || "情境旁白" }}</span>
      <p>
        {{
          activeDialogue?.text ||
          narrator ||
          "选择你的角色，让每一次决定推动故事。"
        }}
      </p>
      <small v-if="playing"
        >字幕演绎 · 角色动作示意 · 点击人物切换对话对象</small
      >
    </div>
    <div class="stage-speakers">
      <button
        v-for="(d, i) in dialogues"
        :key="i"
        :class="{ selected: activeIndex === i }"
        @click="play(i)"
      >
        <span>{{ i + 1 }}</span
        >{{ d.name }}
      </button>
      <label
        >节奏
        <select v-model.number="rate" aria-label="字幕演绎节奏">
          <option :value="0.85">慢速</option>
          <option :value="1">正常</option>
          <option :value="1.15">稍快</option>
        </select></label
      >
    </div>
  </section>
</template>
<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
const props = defineProps({
  roles: { type: Array, default: () => [] },
  dialogues: { type: Array, default: () => [] },
  narrator: String,
  sceneType: { type: String, default: "school" },
});
const emit = defineEmits(["select-role"]);
const host = ref(null),
  flat = ref(false),
  failed = ref(false),
  ready = ref(false),
  playing = ref(false),
  activeIndex = ref(0),
  rate = ref(1);
const outfits = ["#304d68", "#21877c", "#ae745c", "#6a648b"];
const activeDialogue = computed(() => props.dialogues[activeIndex.value]);
const sceneLabel = computed(
  () =>
    ({
      school: "校园",
      court: "模拟法庭",
      home: "社区",
      security: "网络安全",
      tech: "科技社会",
    })[props.sceneType] || "情境",
);
const speakerIndex = computed(() => {
  const name = activeDialogue.value?.name || "";
  const matched = props.roles.findIndex(
    (r) => name.includes(r.name) || r.name.includes(name),
  );
  return matched >= 0
    ? matched
    : activeIndex.value % Math.max(1, props.roles.length);
});
let renderer,
  scene,
  camera,
  observer,
  THREE,
  timer,
  runId = 0,
  frameLoop,
  lastTime = 0,
  elapsed = 0,
  characters = [],
  moving = [],
  geometries = new Set(),
  materials = new Set(),
  textures = new Set();
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
function stop() {
  runId++;
  playing.value = false;
  clearTimeout(timer);
}
function play(index = 0) {
  stop();
  if (!props.dialogues.length) return;
  activeIndex.value = Math.max(0, Math.min(index, props.dialogues.length - 1));
  playing.value = true;
  const token = runId;
  const line = props.dialogues[activeIndex.value];
  function next() {
    if (token !== runId) return;
    clearTimeout(timer);
    if (activeIndex.value + 1 < props.dialogues.length)
      play(activeIndex.value + 1);
    else playing.value = false;
  }
  timer = setTimeout(
    next,
    Math.max(2500, (line.text.length / (6 * rate.value)) * 1000),
  );
}
watch(
  () => props.dialogues,
  () => {
    stop();
    activeIndex.value = 0;
  },
  { deep: true },
);
watch(flat, () => {
  if (renderer) renderer.setAnimationLoop(flat.value ? null : frameLoop);
});
function mesh(geo, color, x = 0, y = 0, z = 0, parent = scene) {
  const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.8 });
  const obj = new THREE.Mesh(geo, mat);
  geometries.add(geo);
  materials.add(mat);
  obj.position.set(x, y, z);
  obj.castShadow = true;
  obj.receiveShadow = true;
  parent.add(obj);
  return obj;
}
function box(w, h, d, color, x, y, z, parent = scene) {
  return mesh(new THREE.BoxGeometry(w, h, d), color, x, y, z, parent);
}
function sphere(r, color, x, y, z, parent) {
  return mesh(new THREE.SphereGeometry(r, 16, 12), color, x, y, z, parent);
}
function label(text, parent) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 96;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "rgba(255,255,255,.94)";
  ctx.beginPath();
  ctx.roundRect(4, 4, 504, 88, 22);
  ctx.fill();
  ctx.fillStyle = "#243c4b";
  ctx.font = "600 37px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text.slice(0, 10), 256, 48);
  const texture = new THREE.CanvasTexture(canvas);
  textures.add(texture);
  const material = new THREE.SpriteMaterial({ map: texture, depthTest: false });
  materials.add(material);
  const sprite = new THREE.Sprite(material);
  sprite.position.set(0, 2.12, 0);
  sprite.scale.set(1.4, 0.263, 1);
  parent.add(sprite);
}
function person(role, index, total) {
  const group = new THREE.Group();
  group.position.set(
    (index - (total - 1) / 2) * 1.68,
    0,
    0.15 + (index % 2) * 0.2,
  );
  group.rotation.y = (index - (total - 1) / 2) * -0.1;
  scene.add(group);
  const skin = ["#e4b38b", "#c68f69", "#efc8a6", "#cda17d"][index % 4],
    shirt = outfits[index % outfits.length];
  mesh(new THREE.CapsuleGeometry(0.26, 0.48, 5, 12), shirt, 0, 0.96, 0, group);
  box(0.11, 0.45, 0.12, "#f0e9db", 0, 1.04, 0.255, group);
  box(0.055, 0.34, 0.05, "#bd8b4e", 0, 1.0, 0.325, group);
  const head = new THREE.Group();
  head.position.y = 1.57;
  group.add(head);
  sphere(0.26, skin, 0, 0, 0, head);
  const hair = mesh(
    new THREE.SphereGeometry(0.273, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.52),
    "#343339",
    0,
    0.025,
    -0.012,
    head,
  );
  const eyes = [];
  for (const x of [-0.09, 0.09]) {
    const eye = sphere(0.035, "#fffdf8", x, 0.02, 0.236, head);
    const pupil = sphere(0.017, "#24313d", x, 0.018, 0.265, head);
    eyes.push(eye, pupil);
  }
  sphere(0.035, skin, 0, -0.045, 0.261, head);
  const mouth = mesh(
    new THREE.SphereGeometry(0.055, 12, 8),
    "#6e3a36",
    0,
    -0.11,
    0.243,
    head,
  );
  mouth.scale.set(1, 0.16, 0.32);
  for (const x of [-0.14, 0.14]) {
    mesh(
      new THREE.CapsuleGeometry(0.09, 0.43, 4, 8),
      "#293b4a",
      x,
      0.36,
      0,
      group,
    );
    const shoe = sphere(0.12, "#263743", x, 0.08, 0.07, group);
    shoe.scale.set(1, 0.55, 1.6);
  }
  const arms = [];
  for (const side of [-1, 1]) {
    const arm = new THREE.Group();
    arm.position.set(side * 0.33, 1.19, 0);
    arm.rotation.z = side * 0.16;
    group.add(arm);
    mesh(new THREE.CapsuleGeometry(0.075, 0.35, 4, 8), shirt, 0, -0.25, 0, arm);
    sphere(0.082, skin, 0, -0.49, 0, arm);
    arms.push(arm);
  }
  const ring = mesh(
    new THREE.TorusGeometry(0.46, 0.025, 8, 48),
    "#c1d3c7",
    0,
    0.035,
    0,
    group,
  );
  ring.rotation.x = -Math.PI / 2;
  label(role.name, group);
  group.userData.roleName = role.name;
  characters.push({
    group,
    head,
    mouth,
    arms,
    eyes,
    ring,
    baseY: group.position.y,
    phase: index * 1.8,
  });
}
function buildSet() {
  const campus = props.sceneType === "school",
    court = props.sceneType === "court";
  mesh(
    new THREE.PlaneGeometry(18, 13),
    campus ? "#dce9dd" : "#e8dfd2",
    0,
    -0.015,
    0,
  ).rotation.x = -Math.PI / 2;
  box(15, 5, 0.18, campus ? "#f1e8d7" : "#ece8de", 0, 2.45, -3.5);
  for (const x of [-4.6, 4.6]) {
    box(2.7, 2.25, 0.12, "#b4d6e0", x, 2.65, -3.34);
    box(2.9, 0.1, 0.2, "#fffdf5", x, 3.82, -3.2);
    box(0.08, 2.35, 0.15, "#fffdf5", x, 2.65, -3.2);
    box(2.8, 0.08, 0.15, "#fffdf5", x, 2.65, -3.2);
    const cloud = new THREE.Group();
    scene.add(cloud);
    for (let j = 0; j < 3; j++) {
      const c = sphere(
        0.22 + j * 0.035,
        "#f7fbf8",
        x + j * 0.27 - 0.3,
        3.15 + Math.sin(j) * 0.07,
        -3.1,
        cloud,
      );
      c.scale.y = 0.65;
    }
    moving.push({
      object: cloud,
      type: "cloud",
      base: cloud.position.x,
      phase: x,
    });
  }
  if (campus) {
    box(4, 1.65, 0.15, "#2e675d", 0, 2.75, -3.3);
    box(4.3, 0.11, 0.24, "#b59a73", 0, 1.88, -3.18);
    for (let i = 0; i < 4; i++)
      box(
        1.1 + (i % 2) * 0.6,
        0.035,
        0.025,
        "#c9dcd3",
        -0.6,
        3.2 - i * 0.26,
        -3.2,
      );
    for (const x of [-3.7, 3.7]) {
      box(1.8, 0.13, 0.7, "#b78f69", x, 0.52, -1.65);
      for (const y of [-0.55, 0.55])
        box(0.1, 0.5, 0.1, "#647c77", x + y, 0.25, -1.65);
    }
  } else if (court) {
    box(4.8, 0.95, 0.8, "#a78463", 0, 0.5, -2.3);
    box(5.1, 0.12, 1, "#6b5344", 0, 1.03, -2.3);
    for (const x of [-2.6, 2.6])
      mesh(
        new THREE.CylinderGeometry(0.18, 0.23, 3.4, 12),
        "#d0bda5",
        x,
        1.7,
        -3.1,
      );
  } else {
    box(3.4, 0.52, 0.8, "#7a9d96", 0, 0.32, -2.5);
    box(3.4, 0.65, 0.15, "#8eafa5", 0, 0.8, -2.85);
    box(1.7, 0.12, 0.8, "#b59a78", 0, 0.45, -1.45);
    box(0.7, 0.45, 0.05, "#365164", 0, 0.73, -1.5);
  }
  for (const x of [-5.3, 5.3]) {
    const plant = new THREE.Group();
    plant.position.set(x, 0, -1.6);
    scene.add(plant);
    mesh(
      new THREE.CylinderGeometry(0.32, 0.23, 0.5, 12),
      "#c89675",
      0,
      0.25,
      0,
      plant,
    );
    mesh(
      new THREE.CylinderGeometry(0.035, 0.05, 1, 8),
      "#8c7954",
      0,
      0.9,
      0,
      plant,
    );
    for (let j = 0; j < 4; j++) {
      const leaf = sphere(
        0.35,
        j % 2 ? "#83ac85" : "#598c72",
        Math.cos(j * 2) * 0.24,
        1.3 + j * 0.12,
        Math.sin(j) * 0.2,
        plant,
      );
      leaf.scale.set(1, 1.3, 0.7);
    }
    moving.push({ object: plant, type: "plant", phase: x });
  }
}
async function setup() {
  try {
    THREE = await import("three");
    if (!host.value) return;
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: "low-power",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    host.value.appendChild(renderer.domElement);
    renderer.domElement.addEventListener("webglcontextlost", contextLost);
    renderer.domElement.addEventListener("pointerdown", selectCharacter);
    scene = new THREE.Scene();
    scene.background = new THREE.Color("#f0ece3");
    scene.fog = new THREE.Fog("#f0ece3", 14, 25);
    camera = new THREE.PerspectiveCamera(36, 1, 0.1, 60);
    camera.position.set(5.8, 3.5, 8.2);
    camera.lookAt(0, 1.05, -0.4);
    camera.zoom = 1.12;
    camera.updateProjectionMatrix();
    scene.add(new THREE.HemisphereLight("#fff7e7", "#718e85", 2.0));
    const light = new THREE.DirectionalLight("#fff2d5", 2.0);
    light.position.set(-4, 9, 5);
    light.castShadow = true;
    light.shadow.mapSize.set(1024, 1024);
    light.shadow.camera.left = -9;
    light.shadow.camera.right = 9;
    light.shadow.camera.top = 7;
    light.shadow.camera.bottom = -7;
    scene.add(light);
    buildSet();
    const roles = props.roles.length
      ? props.roles.slice(0, 4)
      : [{ name: "主持人" }, { name: "参与者" }, { name: "见证人" }];
    roles.forEach((r, i) => person(r, i, roles.length));
    function resize() {
      if (!host.value || !renderer) return;
      const { width, height } = host.value.getBoundingClientRect();
      if (!width || !height) return;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }
    observer = new ResizeObserver(resize);
    observer.observe(host.value);
    resize();
    frameLoop = (timestamp) => {
      const dt = Math.min(0.05, Math.max(0, (timestamp - lastTime) / 1000));
      lastTime = timestamp;
      elapsed += dt;
      const time = elapsed;
      characters.forEach((c, i) => {
        const talk = playing.value && speakerIndex.value === i;
        c.mouth.scale.y = talk
          ? 0.4 + Math.abs(Math.sin(time * 13) * Math.sin(time * 7)) * 2.4
          : 0.16;
        if (!reduced) {
          c.group.position.y = c.baseY + Math.sin(time * 1.7 + c.phase) * 0.012;
          c.head.rotation.x = talk ? Math.sin(time * 3.1) * 0.07 : 0.01;
          c.arms[1].rotation.z = talk
            ? -0.45 + Math.sin(time * 2.4) * 0.17
            : -0.16;
          c.arms[0].rotation.x = talk ? Math.sin(time * 2) * 0.1 : 0;
        }
        const blink = Math.sin(time * 1.4 + c.phase) > 0.996 ? 0.18 : 1;
        c.eyes.forEach((e) => {
          e.scale.y = blink;
        });
        c.ring.material.color.set(talk ? "#15a18b" : "#c1d3c7");
      });
      if (!reduced)
        moving.forEach((m) => {
          if (m.type === "plant")
            m.object.rotation.z = Math.sin(time * 0.7 + m.phase) * 0.025;
          else m.object.position.x = Math.sin(time * 0.15 + m.phase) * 0.13;
        });
      renderer.render(scene, camera);
    };
    renderer.setAnimationLoop(frameLoop);
    ready.value = true;
  } catch (_) {
    failed.value = true;
    ready.value = true;
    renderer?.setAnimationLoop(null);
  }
}
function selectCharacter(event) {
  if (!renderer || !camera) return;
  const rect = renderer.domElement.getBoundingClientRect();
  const ray = new THREE.Raycaster();
  ray.setFromCamera(
    new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      (-(event.clientY - rect.top) / rect.height) * 2 + 1,
    ),
    camera,
  );
  const hits = ray.intersectObjects(
    characters.map((c) => c.group),
    true,
  );
  if (!hits.length) return;
  let node = hits[0].object;
  while (node && !node.userData.roleName) node = node.parent;
  if (!node) return;
  emit("select-role", node.userData.roleName);
  const index = props.dialogues.findIndex(
    (d) => d.name === node.userData.roleName,
  );
  if (index >= 0) play(index);
}
function contextLost(event) {
  event.preventDefault();
  failed.value = true;
  renderer?.setAnimationLoop(null);
}
function visibility() {
  if (document.hidden) {
    stop();
    renderer?.setAnimationLoop(null);
  } else if (!flat.value && !failed.value)
    renderer?.setAnimationLoop(frameLoop);
}
onMounted(() => {
  setup();
  document.addEventListener("visibilitychange", visibility);
});
onBeforeUnmount(() => {
  stop();
  document.removeEventListener("visibilitychange", visibility);
  observer?.disconnect();
  renderer?.setAnimationLoop(null);
  renderer?.domElement.removeEventListener("webglcontextlost", contextLost);
  renderer?.domElement.removeEventListener("pointerdown", selectCharacter);
  geometries.forEach((g) => g.dispose());
  materials.forEach((m) => m.dispose());
  textures.forEach((t) => t.dispose());
  renderer?.dispose();
});
</script>
