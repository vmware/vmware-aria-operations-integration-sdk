/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */
package com.vmware.aria.operations

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
class SuiteApiClient(
    @SerialName("host_name") val hostname: String,
    @SerialName("user_name") val username: String,
    private val password: String,
) {

}
