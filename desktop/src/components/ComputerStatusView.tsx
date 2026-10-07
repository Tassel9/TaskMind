/** Computer Runtime 与权限的紧凑产品状态。 */

import { leaseLabel } from '../api/computer'
import type {
  ComputerPermissionName,
  ComputerStatus,
} from '../api/computer'
import { StatusDot } from './ui'

export default function ComputerStatusView({
  status,
  loading = false,
}: {
  status: ComputerStatus | null
  loading?: boolean
  onRequestPermission?: (permission: ComputerPermissionName) => void
}): React.JSX.Element {
  if (loading && !status) return <div className="loading-inline"><span className="spinner" /> 正在检查电脑操作状态…</div>
  if (!status) return <div className="empty-inline empty-inline--error">无法获取电脑操作状态</div>

  const reason = status.reason === 'helper_not_found'
    ? '未找到 Windows helper'
    : status.reason === 'helper_dependency_missing'
      ? '缺少 helper 运行依赖'
      : status.reason === 'unsupported_platform'
        ? `不支持当前平台（${status.platform}）`
        : status.reason
  const runtimeLabel = status.runtime === 'windows'
    ? 'Windows'
    : status.runtime ?? '未知'

  return (
    <div className="computer-status-view">
      <div className="computer-status-view__runtime">
        <StatusDot tone={status.available ? 'ready' : 'failed'} />
        <div>
          <strong>{status.available ? '可用' : '不可用'}</strong>
          <span>
            {status.available
              ? `电脑操作运行时 · ${runtimeLabel}`
              : reason ?? '运行时不可用'}
          </span>
        </div>
        <small>{leaseLabel(status.lease)}</small>
      </div>
      {status.platform === 'win32' ? (
        <p className="empty-inline">Windows 上无需辅助功能或屏幕录制授权。</p>
      ) : null}
      {status.helper_path ? (
        <details className="technical-inline">
          <summary>运行时详情</summary>
          <code>{status.helper_path}</code>
        </details>
      ) : null}
    </div>
  )
}
