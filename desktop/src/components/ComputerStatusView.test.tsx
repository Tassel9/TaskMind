/** ComputerStatusView 渲染测试（renderToStaticMarkup，无 DOM）。 */

import { describe, expect, it } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'

import type { ComputerStatus } from '../api/computer'
import ComputerStatusView from './ComputerStatusView'

const status: ComputerStatus = {
  enabled: true,
  available: true,
  platform: 'win32',
  runtime: 'windows',
  reason: null,
  helper_path: null,
  permissions: { accessibility: 'granted', screen_recording: 'required' },
  lease: { busy: false, owner_run_id: '', acquired_at: null, process_id: 1 },
}

describe('ComputerStatusView', () => {
  it('available 渲染 Windows 运行时状态', () => {
    const html = renderToStaticMarkup(<ComputerStatusView status={status} />)
    expect(html).toContain('可用')
    expect(html).toContain('电脑操作运行时 · Windows')
    expect(html).not.toContain('permission-row')
    expect(html).toContain('空闲')
  })

  it('unavailable 渲染 reason', () => {
    const html = renderToStaticMarkup(
      <ComputerStatusView
        status={{
          ...status,
          available: false,
          reason: 'helper_not_found',
          permissions: { accessibility: 'unknown', screen_recording: 'unknown' },
          lease: null,
        }}
      />,
    )
    expect(html).toContain('不可用')
    expect(html).toContain('未找到 Windows helper')
    expect(html).toContain('空闲')
  })

  it('Windows 不显示系统权限请求按钮', () => {
    const html = renderToStaticMarkup(
      <ComputerStatusView status={status} onRequestPermission={() => {}} />,
    )
    expect(html).not.toContain('请求权限')
  })

  it('无 handler 时不显示 Request 按钮', () => {
    const html = renderToStaticMarkup(<ComputerStatusView status={status} />)
    expect(html).not.toContain('Request')
  })

  it('Windows 平台显示运行时标签且不显示权限授权行', () => {
    const html = renderToStaticMarkup(
      <ComputerStatusView
        status={{
          ...status,
          platform: 'win32',
          runtime: 'windows',
          permissions: { accessibility: 'granted', screen_recording: 'granted' },
        }}
      />,
    )
    expect(html).toContain('电脑操作运行时 · Windows')
    expect(html).toContain('Windows 上无需辅助功能或屏幕录制授权。')
    expect(html).not.toContain('permission-row')
  })

  it('缺少 helper 依赖时显示依赖提示', () => {
    const html = renderToStaticMarkup(
      <ComputerStatusView
        status={{
          ...status,
          available: false,
          reason: 'helper_dependency_missing',
          permissions: { accessibility: 'unknown', screen_recording: 'unknown' },
        }}
      />,
    )
    expect(html).toContain('缺少 helper 运行依赖')
  })
})
