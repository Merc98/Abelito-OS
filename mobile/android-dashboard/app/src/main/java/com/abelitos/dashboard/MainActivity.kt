package com.abelitos.dashboard

import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.Toolbar
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.widget.Button
import android.widget.ProgressBar

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var pageLoadProgress: ProgressBar
    private lateinit var loadingSpinner: ProgressBar
    private lateinit var errorView: View

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val toolbar: Toolbar = findViewById(R.id.toolbar)
        setSupportActionBar(toolbar)
        toolbar.setNavigationIcon(android.R.drawable.ic_media_previous)

        webView = findViewById(R.id.dashboardWebView)
        pageLoadProgress = findViewById(R.id.pageLoadProgress)
        loadingSpinner = findViewById(R.id.loadingSpinner)
        errorView = findViewById(R.id.errorView)

        val retryButton: Button = findViewById(R.id.retryButton)
        retryButton.setOnClickListener { reloadChat() }

        toolbar.setNavigationOnClickListener {
            if (webView.canGoBack()) webView.goBack() else finish()
        }

        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true

        webView.webViewClient = object : WebViewClient() {
            override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                super.onPageStarted(view, url, favicon)
                showLoading(true)
                showError(false)
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                showLoading(false)
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: WebResourceError,
            ) {
                super.onReceivedError(view, request, error)
                if (request.isForMainFrame) {
                    showLoading(false)
                    showError(true)
                }
            }

            override fun onReceivedHttpError(
                view: WebView,
                request: WebResourceRequest,
                errorResponse: WebResourceResponse,
            ) {
                super.onReceivedHttpError(view, request, errorResponse)
                if (request.isForMainFrame && errorResponse.statusCode >= 400) {
                    showLoading(false)
                    showError(true)
                }
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                super.onProgressChanged(view, newProgress)
                pageLoadProgress.progress = newProgress
                pageLoadProgress.visibility = if (newProgress in 1..99) View.VISIBLE else View.GONE
                loadingSpinner.visibility = if (newProgress in 1..99) View.VISIBLE else View.GONE
            }
        }

        reloadChat()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_refresh -> {
                webView.reload()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    private fun reloadChat() {
        showError(false)
        showLoading(true)
        webView.loadUrl(CHAT_URL)
    }

    private fun showLoading(isLoading: Boolean) {
        loadingSpinner.visibility = if (isLoading) View.VISIBLE else View.GONE
        if (!isLoading) {
            pageLoadProgress.visibility = View.GONE
        }
    }

    private fun showError(show: Boolean) {
        errorView.visibility = if (show) View.VISIBLE else View.GONE
        webView.visibility = if (show) View.GONE else View.VISIBLE
    }

    private companion object {
        private const val CHAT_URL = "http://10.0.2.2:8080/dashboard"
    }
}
