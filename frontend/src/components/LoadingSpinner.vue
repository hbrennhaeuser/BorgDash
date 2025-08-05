<template>
  <div class="flex items-center justify-center" :class="containerClass">
    <div
      class="animate-spin rounded-full border-2 border-current border-t-transparent"
      :class="spinnerClass"
    ></div>
    <span v-if="text" class="ml-2 text-sm text-gray-600">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  containerClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  text: '',
  containerClass: ''
})

const spinnerClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-4 w-4'
    case 'lg':
      return 'h-8 w-8'
    default:
      return 'h-6 w-6'
  }
})
</script>

<script lang="ts">
import { computed } from 'vue'
export default {
  name: 'LoadingSpinner'
}
</script>
