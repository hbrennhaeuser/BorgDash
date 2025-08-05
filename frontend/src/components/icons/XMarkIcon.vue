<template>
  <svg
    class="inline-block"
    :class="[`h-${size} w-${size}`]"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="2"
      d="M6 18L18 6M6 6l12 12"
    />
  </svg>
</template>

<script setup lang="ts">
interface Props {
  size?: number
}

withDefaults(defineProps<Props>(), {
  size: 6
})
</script>
