<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { mountChart } from '../../assignment4/chart.js'

const props = defineProps({ rows: { type: Array, default: () => [] }, product: { type: String, required: true },
  fastWindow: { type: Number, default: 5 }, slowWindow: { type: Number, default: 20 } })
const container = ref(null)
let view
onMounted(() => { view = mountChart(container.value); view.update(props.rows, props.product, props.fastWindow, props.slowWindow) })
watch(() => [props.rows, props.product, props.fastWindow, props.slowWindow],
  () => view?.update(props.rows, props.product, props.fastWindow, props.slowWindow), { deep: true })
onUnmounted(() => { view?.remove(); view = null })
</script>

<template>
  <div class="chart-surface" role="figure" :aria-label="product === 'interval' ? 'Yahoo interval candlesticks with matching provider-reported volume' : 'Stream-observed candlesticks; volume unknown'">
    <div ref="container" />
    <button class="fit" @click="view?.fit()">Fit chart</button>
  </div>
</template>

<style scoped>
.chart-surface { position: relative; min-height: 390px; }
.fit { position: absolute; left: 14px; top: 10px; z-index: 1; padding: 5px 10px; font-size: 12px; background: #fffefbe8; }
</style>
